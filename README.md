# NUS-MODerator
## 1. Introduction
NUS-MODerator is a project that began in April 2025. Hosted on Streamlit Community Cloud, it is a web application that serves as a tool to assist NUS students in their schooling.

### 1.1 Current Features
- **Bus Services**: Displays live bus updates for bus stops on campus. Users can also use the app to record their bus trips (for NUS bus services only)
- **Course Planner**: Allows users to plan their courses, up until the current academic year. Takes prerequisites and modular credit (MC) requirements into account. Users can also save their completed course plans to their profiles
- **AMA**: A chatbot that answers questions on NUS courses. Uses LangChain to perform retrieval augmented generation on NUSMods reviews
- **Profile Page**: Displays the courses that the user has saved to his / her profile. Users can also rate their courses on a scale of 0-10

### 1.2 Potential Future Work
- Conduct data visualisation on the bus trip data collected
- Use the bus trip data collected to forecast demand for NUS bus services
- Use the course ratings collected to create a module recommendation system

Of course, since these goals are very much data-driven, it all depends on whether or not there are enough people using the application :D

## 2. How to Use
1. Visit the website at https://nus-moderator.streamlit.app/
2. Register, log in and have fun!