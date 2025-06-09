from moderator.config import AVERAGE_MCS_PER_AY, MAX_MCS_FIRST_SEM
from moderator.sql.credit_internships import GET_CREDIT_INTERNSHIPS_QUERY
from moderator.sql.majors import GET_EXISTING_MAJOR_QUERY
from moderator.sql.modules import GET_SPECIFIC_TERM_MODULES_QUERY, GET_MODULES_INFO_FOR_PLANNER_QUERY, GET_TERMS_OFFERED_FOR_SPECIFIC_MODULE_QUERY
from moderator.utils.helpers import get_semester_info
from moderator.utils.user import User
import numpy as np
import re
import requests
import streamlit as st


class CoursePlanChecker(object):
    ### FUNCTIONS FOR CHECKER INITIALISATION ###    
    def get_credit_internships(self) -> set[str]:
        # Query the modules that are credit-bearing internships
        credit_internships = set(
            self._conn.query(
                GET_CREDIT_INTERNSHIPS_QUERY,
                ttl=3600
            )["internship_code"]
        )

        return credit_internships


    def get_module_infos(self) -> dict[str, dict[str, float | bool]]:
        rows_queried = self._conn.query(
            GET_MODULES_INFO_FOR_PLANNER_QUERY,
            ttl=3600
        ).values.tolist()

        # Maps each module to its number of MCs, and whether or not it is year-long
        module_infos = {
            module_code: {
                "num_mcs": float(num_mcs),
                "is_year_long": is_year_long
            } for module_code, num_mcs, is_year_long in rows_queried
        }

        return module_infos


    def __init__(self, conn: st.connections.SQLConnection, user: User, list_of_ays: list[str]):
        # Assign connection as an attribute
        self._conn = conn

        # Get number of years that user is required to study for, based on his / her major
        self._num_years_to_grad = self._conn.query(
            GET_EXISTING_MAJOR_QUERY,
            params={
                "major": user.major
            },
            ttl=3600
        ).iloc[0]["num_years"]

        # Assign other relevant parameters for course checking
        self._max_mcs_first_sem = MAX_MCS_FIRST_SEM      # Max number of MCs that can be taken in user's first semester
        self._min_mcs_to_grad = self._num_years_to_grad * AVERAGE_MCS_PER_AY      # Min number of MCs needed to graduate. On average, 40 MCs are taken per year

        # Get the AYs during which the user will be studying (capped off by current AY)
        first_ay = user.matriculation_ay
        first_ay_index = list_of_ays.index(first_ay)
        self._ays_for_user = list_of_ays[first_ay_index: first_ay_index + self._num_years_to_grad]

        # Get module info required for planner
        # Maps each module to its number of MCs, and whether or not it is year-long
        self._module_infos = self.get_module_infos()

        # Get semester info (list) in the form (sem_num, sem_name, min_mcs)
        self._sem_info = get_semester_info(conn=self._conn)

        # Get list of credit-bearing internships
        self._credit_internships = self.get_credit_internships()

        # Initialise default selections for selectboxes (memorise user's choices)
        # Structure: Keys are AYs. Values are themselves dictionaries, with keys = sem_num and 
        # values = list of default module names for that semester's selectbox
        self._course_default_selections = {ay: {sem_num: list() for sem_num, _, _ in self._sem_info} for ay in self._ays_for_user}

        # Will keep track of the plan, building it iteratively, based on the user's selections for each term
        # Structure: Keys are AYs. Values are themselves dictionaries, with keys = sem_num and values = list of module codes for that term
        # NOTE: If this is None, it means the plan has already become invalid somewhere along the line
        self._plan = dict()

        # Initialise dictionary of plans that have already been checked for their validity
        # Keys: Tuple of frozensets, one frozenset per term representing the set of module codes
        # taken that term. Frozensets are in chronological order of terms
        # Values: A dictionary consisting of the type of Streamlit display message that the user will receive, alongside the message content
        self._course_plans_checked = dict()

        # Track total number of MCs taken
        self._total_mcs_taken = 0.0


    ### GETTERS ###
    @property
    def ays_for_user(self) -> list[str]:
        return self._ays_for_user
    

    @property
    def sem_info(self) -> list[list[int | str | np.float64]]:
        return self._ays_for_user
    

    @property
    def plan(self) -> dict[str, dict[int, list[str]]]:
        return self._plan
    

    @property
    def total_mcs_taken(self) -> float:
        return self._total_mcs_taken
    

    @property
    def course_default_selections(self) -> dict[str, dict[int, list[str]]]:
        return self._course_default_selections
    

    @property
    def min_mcs_to_grad(self) -> float:
        return self._min_mcs_to_grad
    

    ### MANAGING COURSE PLANS IN DIFFERENT FORMATS ###
    def convert_plan_to_frozenset_format(self) -> tuple[frozenset[str]]:
        # Structure of frozenset format: Tuple of frozensets, one frozenset per term representing the set of module codes
        # taken that term. Frozensets are in chronological order of terms
        frozensets_of_module_codes = list()
        for acad_year, acad_year_plan in self._plan.items():
            for sem_num, module_codes in acad_year_plan.items():
                module_codes_for_term = frozenset(module_codes)
                frozensets_of_module_codes.append(module_codes_for_term)
        
        return tuple(frozensets_of_module_codes)
    

    ### MANAGE DEFAULT SELECTBOX SELECTIONS ###
    def get_default_selection_for_term_during_check(self, acad_year: str, sem_num: int) -> list[str]:
        # If plan is already invalid, set default options for selectbox to an empty list
        if self._plan is None:
            self._course_default_selections[acad_year][sem_num] = list()

        return self._course_default_selections[acad_year][sem_num]
    

    def set_default_selection_for_term(self, acad_year: str, sem_num: int, new_default_selection: list[str]) -> None:
        self._course_default_selections[acad_year][sem_num] = new_default_selection


    # If a default selection is edited, make sure to remove these modules from subsequent default selections
    # This ensures default selections never include module names from earlier default selections
    def remove_edited_selection_from_subsequent_selections(self, edited_selection: list[str], subsequent_selection_acad_year: str, subsequent_selection_sem_num: int) -> None:
        subsequent_selection = self._course_default_selections[subsequent_selection_acad_year][subsequent_selection_sem_num]
        for module_name in edited_selection:
            if module_name in subsequent_selection:
                subsequent_selection.remove(module_name)
    

    # If a default selection is edited, we want to ensure that the AY is consistent, with regards to year-long modules
    # For another term in that AY (chosen by us), update the default selection for that term such that this consistency is maintained
    def ensure_year_long_consistency(self, acad_year: str, edited_sem_num: int, edited_selection: list[str], target_sem_num: int) -> None:
        # Get default selection for the target semester
        target_selection = self._course_default_selections[acad_year][target_sem_num]
        
        # Get the year-long module names in the selectbox edited, each mapped to the terms that it is offered
        year_long_module_names_in_edited_selection = dict()
        for edited_module_name in edited_selection:
            edited_module_code = edited_module_name.split()[0]
            edited_module_is_year_long = self._module_infos[edited_module_code]["is_year_long"]
            if edited_module_is_year_long:
                # Get the sem_nums in which this year-long module is being offered, for this AY
                terms_offered = self.get_terms_offered_for_module(module_code=edited_module_code, acad_year=acad_year)
                
                # Update mapping
                year_long_module_names_in_edited_selection[edited_module_name] = terms_offered

        # Get new list of module names for the target selection
        new_target_selection = list()
        for target_module_name in target_selection:
            target_module_code = target_module_name.split()[0]
            target_module_is_year_long = self._module_infos[target_module_code]["is_year_long"]
            if target_module_is_year_long:
                # Get the sem_nums in which this year-long module is being offered, for this AY
                target_module_terms_offered = self.get_terms_offered_for_module(module_code=target_module_code, acad_year=acad_year)

                if edited_sem_num in target_module_terms_offered and target_module_name not in year_long_module_names_in_edited_selection:
                    # Year-long module in target selection is also offered in the term corresponding to the edited selection,
                    # but it is not in the edited selection. Must remove it from target selection
                    continue

            # Module should still stay in the target selection
            new_target_selection.append(target_module_name)

        # Add new year-long modules from the edited selection into the target selection,
        # if these modules are also offered in the term corresponding to the target selection
        for year_long_module_name, year_long_module_terms_offered in year_long_module_names_in_edited_selection.items():
            if year_long_module_name not in new_target_selection and target_sem_num in year_long_module_terms_offered:
                new_target_selection.append(year_long_module_name)
        
        # Update target selection
        self._course_default_selections[acad_year][target_sem_num] = new_target_selection


    ### RESET CHECKER ###
    def reset(self) -> None:
        # Reset the course plan built and the total number of MCs
        self._plan = dict()
        self._total_mcs_taken = 0.0


    ### PREPARATION FOR USER'S COURSE SELECTION ###
    def get_available_modules_for_term(self, acad_year: str, sem_num: int) -> list[list[str]]:
        # Query the modules available for the selected term - a list of lists in the form (module_code, module_title)
        available_modules = self._conn.query(
            GET_SPECIFIC_TERM_MODULES_QUERY,
            params={
                "acad_year": acad_year,
                "sem_num": sem_num
            },
            ttl=3600
        ).values.tolist()

        return available_modules
    

    def get_completed_module_codes_from_plan(self) -> list[str]:
        completed_module_codes = list()

        for acad_year, acad_year_plan in self._plan.items():
            for sem_num, module_codes in acad_year_plan.items():
                # We have already ensured that there will never be repeated module codes across the terms (except for year-long modules)
                # This is because user will only choose among modules that they have not taken yet
                completed_module_codes.extend(module_codes)

        return completed_module_codes


    def get_list_of_mod_choices_for_term(self, acad_year: str, sem_num: int) -> list[str]:
        # If current plan is None (already invalid), there should be no selections given
        if self._plan is None:
            return list()
        
        # Get previous term's selection of modules
        if not self._plan:
            # If plan is empty (current term is the very first term), set previous term's module selection is empty
            previous_term_ay = None
            previous_term_sem_num = None
            previous_term_module_selection = list()

        else:
            previous_term_ay = sorted(self._plan.keys())[-1]
            previous_term_sem_num = sorted(self._plan[previous_term_ay].keys())[-1]
            previous_term_module_selection = self._plan[previous_term_ay][previous_term_sem_num]

        # Get modules offered for this term in this AY - a list of lists in the form (module_code, module_title)
        available_modules = self.get_available_modules_for_term(acad_year=acad_year, sem_num=sem_num)

        # Get list of module codes completed already
        completed_module_codes = self.get_completed_module_codes_from_plan()

        # Get list of formatted names corresponding to all the remaining modules that have not been taken yet
        module_name_selections = list()
        for module_code, module_title in available_modules:
            if module_code in completed_module_codes:
                # Edge case to handle: Module has been completed already, but...
                # - It is a year-long module
                # - It was taken in the previous term
                # - The previous term is still in the same academic year as this current term
                # Which means this module should still be taken this term
                module_is_year_long = self._module_infos[module_code]["is_year_long"]
                if not (module_is_year_long and module_code in previous_term_module_selection and previous_term_ay == acad_year):
                    # Not the edge case - skip this module as it should not be taken this term
                    continue

            formatted_module_name = f"{module_code} {module_title}"
            module_name_selections.append(formatted_module_name)

        return module_name_selections
    

    ### GET DETAILS OF USER'S SELECTION ###
    def get_terms_offered_for_module(self, module_code: str, acad_year: str) -> list[int]:
        # Query the semester numbers that have the given module
        terms_offered = list(
            self._conn.query(
                GET_TERMS_OFFERED_FOR_SPECIFIC_MODULE_QUERY,
                params={
                    "module_code": module_code,
                    "acad_year": acad_year
                },
                ttl=3600
            )["sem_num"]
        )

        return terms_offered


    def get_total_mcs_for_term(self, module_codes_for_term: list[str], acad_year: str) -> float:
        total_mcs = 0.0

        # Get number of MCs for each module chosen for the term
        for module_code in module_codes_for_term:
            module_mcs, module_is_year_long = self._module_infos[module_code]["num_mcs"], self._module_infos[module_code]["is_year_long"]

            # If module is year-long, number of MCs should be divided equally across each term that it is being taken
            if module_is_year_long:
                num_sems_taken = len(self.get_terms_offered_for_module(module_code=module_code, acad_year=acad_year))
                module_mcs /= num_sems_taken

            total_mcs += module_mcs

        return total_mcs
    

    ### CHECK USER'S SELECTION ###
    def get_prereq_tree(self, module_code: str, acad_year: str) -> dict | None:
        # NUSMods has no information on prerequisite trees for AY2022-2023. 
        # Use data from AY2023-2024 instead - it's close enough bro
        if acad_year == "2022-2023":
            acad_year = "2023-2024"

        # Use NUSMods API to get detailed information about the specified module, for the chosen academic year
        nusmods_endpoint_url = f"https://api.nusmods.com/v2/{acad_year}/modules/{module_code}.json"
        response = requests.get(url=nusmods_endpoint_url)

        if response.status_code != 200:
            raise Exception("Unsuccessful request to NUSMods API")

        # Successful GET request
        module_info = response.json()

        if "prereqTree" not in module_info:
            # Module has no prerequisites
            return None

        return module_info["prereqTree"]


    def check_if_prereqs_satisfied(self, prereq_tree: dict | str | None, completed_module_codes: list[str]) -> bool:
        if prereq_tree is None:
            # Base case 1: No prerequisites, vacuously true
            return True
        
        if type(prereq_tree) == str:
            # Base case 2: Tree is simply a module - check if it has been taken already
            # Remove grade. The module code obtained might have %, which is a wildcard
            # Eg. CS1010% = Any module starting with CS1010
            module_code_with_wildcard = prereq_tree.split(":")[0]

            # Change any % sign into the correct regex
            module_code_regex = module_code_with_wildcard.replace("%", ".*")

            # Check for at least one match in the list of completed module codes
            for completed_module_code in completed_module_codes:
                if re.search(module_code_regex, completed_module_code):
                    return True
            
            return False

        # How the next layer of trees are aggregated (can be "and", "or", "nOf")
        [operation,] = list(prereq_tree.keys())

        if operation == "and":
            # Get list of trees in the layer below
            next_layer_trees = prereq_tree[operation]

            for tree in next_layer_trees:
                # For "and" operation, all the next layer trees must be satisfied
                if not self.check_if_prereqs_satisfied(prereq_tree=tree, completed_module_codes=completed_module_codes):
                    return False
            
            return True

        if operation == "or":
            # Get list of trees in the layer below
            next_layer_trees = prereq_tree[operation]

            for tree in next_layer_trees:
                # For "or" operation, at least one of the next layer trees must be satisfied
                if self.check_if_prereqs_satisfied(prereq_tree=tree, completed_module_codes=completed_module_codes):
                    return True
            
            return False

        # Operation is "nOf" - at least n (minimum number of requirements to be fulfilled)
        # Get n and list of trees in the layer below
        min_num_requirements, next_layer_trees = prereq_tree[operation]

        num_requirements_fulfilled = 0

        for tree in next_layer_trees:
            # For "nOf" operation, at least n of the next layer trees must be satisfied
            if self.check_if_prereqs_satisfied(prereq_tree=tree, completed_module_codes=completed_module_codes):
                num_requirements_fulfilled += 1

                if num_requirements_fulfilled == min_num_requirements:
                    return True
        
        return False


    def check_module_selection_for_term(self, acad_year: str, selected_module_codes: list[str], selected_total_mcs: float, sem_min_mcs: float, is_first_sem_for_user: bool) -> dict[str, bool | str]:
        # Returns a dictionary with keys "type" and "message"
        # "type" will be the type of message to be displayed by Streamlit (success / warning / error)
        result = dict()

        # Check if a credit-bearing internship is being taken
        is_taking_cred_internship = False
        for selected_module_code in selected_module_codes:
            if selected_module_code in self._credit_internships:
                is_taking_cred_internship = True

        # Get remaining MCs to clear (before current selection), in order to graduate
        outstanding_mc_balance = self._min_mcs_to_grad - self._total_mcs_taken

        # Check if minimum MC requirement is met. Underloading is only allowed if:
        # - The user, with this selection, meets the graduation requirements, or
        # - The user is taking a credit-bearing internship for the term
        if selected_total_mcs < sem_min_mcs and selected_total_mcs < outstanding_mc_balance and not is_taking_cred_internship:
            result["type"] = "error"
            result["message"] = f"You have not met the minimum requirement of {sem_min_mcs} MCs."
            return result
        
        # If this is user's first semester, there is a limit to how many MCs he / she can take
        # Check if maximum MC requirement is met (ie. for first semester)
        if is_first_sem_for_user and selected_total_mcs > self._max_mcs_first_sem:
            result["type"] = "error"
            result["message"] = f"You have exceeded the limit of {self._max_mcs_first_sem} MCs."
            return result

        # Get the module codes that have already been taken
        completed_module_codes = self.get_completed_module_codes_from_plan()
        
        # Check if prerequisites have already been taken
        # Loop through each module chosen
        module_codes_with_failed_prereqs = list()
        for selected_module_code in selected_module_codes:
            # Get prerequisite tree
            selected_module_prereq_tree = self.get_prereq_tree(module_code=selected_module_code, acad_year=acad_year)

            # Check if prerequisites have been met, for this module
            if not self.check_if_prereqs_satisfied(prereq_tree=selected_module_prereq_tree, completed_module_codes=completed_module_codes):
                # Update list of modules whose prerequisites have not been met
                module_codes_with_failed_prereqs.append(selected_module_code)

        if module_codes_with_failed_prereqs:
            # There are some modules whose prerequisites may not have been taken
            # We can only give a warning and not an error, because checking for prerequisites using trees alone
            # would cause users to incorrectly fail the requirements for some modules

            # Eg. DSA1101 prerequisites: (O Level A Math) OR (MA1301) OR (MA1301FC) OR (MA1301X)
            # The tree only shows (MA1301) OR (MA1301FC) OR (MA1301X), omitting non-modular requirements
            # A student that has not taken these modules can still take DSA1101 if he / she has taken A Math,
            # but he / she will still fail the tree requirements. But it would be unfair to flag an error here

            result["type"] = "warning"
            result["message"] = f"You may not have satisfied the prerequisites for the following courses: {', '.join(module_codes_with_failed_prereqs)}. Please verify before proceeding."
            return result
        
        # Selection is valid
        result["type"] = "success"
        result["message"] = "Course selection satisfies the requirements!"
        
        return result


    def update_checker(self, acad_year: str, sem_num: int, selected_module_codes: list[str], selected_module_names: list[str], selected_total_mcs: float, message_type: str):
        # Update checker based on validation results
        if message_type == "success" or message_type == "warning":
            # Plan is valid - update it
            if acad_year not in self._plan:
                self._plan[acad_year] = dict()

            self._plan[acad_year][sem_num] = selected_module_codes

            # Update total number of MCs taken
            self._total_mcs_taken += selected_total_mcs

            # Update default selection for this selectbox
            self._course_default_selections[acad_year][sem_num] = selected_module_names
        
        else:
            # Plan is invalid - set it to None
            self._plan = None

            # Update default selection for this selectbox
            self._course_default_selections[acad_year][sem_num] = list()


    def handle_user_selection_for_term(self, selected_module_names: list[str], acad_year: str, sem_num: int, sem_min_mcs: float, is_first_sem_for_user: bool) -> tuple[str, str, float]:
        # Get list of selected module codes from the module names
        selected_module_codes = [module_name.split()[0] for module_name in selected_module_names]

        # Get number of MCs in the current selection
        selected_total_mcs = self.get_total_mcs_for_term(module_codes_for_term=selected_module_codes, acad_year=acad_year)

        # Check if plan is already invalid from previous terms
        if self._plan is None:
            message_type = "error"
            message = "Course selections for previous terms are already invalid. Please review."
            return message_type, message, selected_total_mcs

        # Check if user's selection is valid
        # Get course plan with the user's new selection, in frozenset format
        plan_with_new_selection_frozenset = self.convert_plan_to_frozenset_format() + (frozenset(selected_module_codes),)
        
        if plan_with_new_selection_frozenset in self._course_plans_checked:
            # If course plan (with the user's new selection) has already been checked before,
            # simply get the pre-saved result
            # Result comprises of: 
            # - Type of Streamlit display message that the user will receive
            # - The message content
            message_type = self._course_plans_checked[plan_with_new_selection_frozenset]["message_type"]
            message = self._course_plans_checked[plan_with_new_selection_frozenset]["message"]

        else:
            # Check whether or not the new selection is valid
            result = self.check_module_selection_for_term(
                acad_year=acad_year,
                selected_module_codes=selected_module_codes,
                selected_total_mcs=selected_total_mcs,
                sem_min_mcs=sem_min_mcs,
                is_first_sem_for_user=is_first_sem_for_user
            )

            message_type = result["type"]
            message = result["message"]

            # Add course plan with the new selection (frozenset format) to session state for memoisation
            self._course_plans_checked[plan_with_new_selection_frozenset] = {
                "message_type": message_type,
                "message": message
            }
        
        # Update the checker according to the result of the validation
        self.update_checker(
            acad_year=acad_year,
            sem_num=sem_num,
            selected_module_codes=selected_module_codes,
            selected_module_names=selected_module_names,
            selected_total_mcs=selected_total_mcs,
            message_type=message_type
        )

        return message_type, message, selected_total_mcs