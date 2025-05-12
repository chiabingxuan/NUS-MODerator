import os
import streamlit as st

# Display header
st.header("About")

# Display acknowledgements section
st.markdown("### Acknowledgements")
st.markdown("This project was inspired by the course \"Develop LLM powered applications with LangChain\" on [Udemy](https://www.udemy.com/course/langchain/?srsltid=AfmBOop03tO6wEwm2yilQyRcysAl9VAgDja1VH9zKfJX5-N2EgK_JNr5&couponCode=LETSLEARNNOW). Yes, the course is hidden behind a paywall; no, I am not rich. Thankfully, I had free access to Udemy Business throughout my internship at Synapxe. So, I would like to thank Synapxe for hiring me - I genuinely learnt a lot during my time there too.")
st.markdown("Many thanks to the good people at NUSMods for providing me with assistance along the way, such as their guidance on how to access student reviews via the Disqus API.")
st.markdown("Also a big shoutout to my senpai, [Roydon Tay](https://www.linkedin.com/in/roydon-tay/), for helping me out with the LangChain document retrieval process.")
st.markdown("Sadly, it turns out that the name \"NUSModerator\" [has actually been used before](https://github.com/nusmodifications/nusmods/tree/master/packages/nusmoderator). I guess I'm still hopeless when it comes to naming stuff - if I ever have children, may God bless them.")

# Display information section
st.markdown("### About Me")
st.markdown("Yo, I'm Bing Xuan. I'm currently a Year 3 Data Science and Analytics student at the National University of Singapore. Feel free to check out my [LinkedIn](https://www.linkedin.com/in/bing-xuan-chia/) and [GitHub](https://github.com/chiabingxuan)!")