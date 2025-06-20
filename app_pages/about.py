import streamlit as st

# Display header
st.header("About")

# Display app description section
st.markdown("#### What is NUS-MODerator?")
st.markdown("NUS-MODerator is a project that began in April 2025. Hosted on Streamlit Community Cloud, it is a web application that serves as a tool to assist NUS students in their schooling.")
st.markdown(
    """
    The app has the following features:
    - **Bus Services**: Displays live bus updates for bus stops on campus. You can also record your bus trips (for NUS bus services only)
    - **Course Planner**: Allows you to plan your courses, up until the current academic year. Takes prerequisites and modular credit (MC) requirements into account. You can also save your completed course plans to your profile
    - **AMA**: A chatbot that answers questions on NUS courses. Uses LangChain to perform retrieval augmented generation on NUSMods reviews
    - **Profile Page**: Displays the courses that you have saved to your profile. You can also rate your courses on a scale of 0-10
    """
)

# Display acknowledgements section
st.markdown("#### Acknowledgements")
st.markdown("This project was inspired by the course \"Develop LLM powered applications with LangChain\" on [Udemy](https://www.udemy.com/course/langchain/?srsltid=AfmBOop03tO6wEwm2yilQyRcysAl9VAgDja1VH9zKfJX5-N2EgK_JNr5&couponCode=LETSLEARNNOW). Yes, the course is hidden behind a paywall; no, I am not rich. Thankfully, I had access to Udemy Business throughout my internship at Synapxe. So, I would like to thank Synapxe for hiring me - I genuinely learnt a lot during my time there too.")
st.markdown("Many thanks to the people at NUSMods for providing me with assistance along the way, such as their guidance on how to access student reviews via the Disqus API.")
st.markdown("Shoutout to my senpai, [Roydon](https://www.linkedin.com/in/roydon-tay/), for helping me out with LangChain retrieval augmented generation.")
st.markdown("Also a big thank you to my cousin, [Xi En](https://www.linkedin.com/in/xi-en-tan-5b065b1b2/), for teaching me how to host databases on the cloud for free. The man is an actual coding god - bro needs to be stopped.")
st.markdown("Information on bus stops and bus routes is provided by [Li Yang](https://www.linkedin.com/in/hewliyang/), who has given me permission to make use of his \"NUS NextBus Web Client\" [GitHub repository](https://github.com/hewliyang/nus-nextbus-web).")

# Display information section
st.markdown("#### About Me")
st.markdown("Yo, I'm Bing Xuan. I'm currently a Year 3 Data Science and Analytics student at the National University of Singapore. Feel free to check out my [LinkedIn](https://www.linkedin.com/in/bing-xuan-chia/) and [GitHub](https://github.com/chiabingxuan)!")