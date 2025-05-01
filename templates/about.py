from dotenv import load_dotenv
import os
import streamlit as st

load_dotenv()

# Display header
st.header("About")

# Display acknowledgements section
st.markdown("### Acknowledgements")
st.markdown("Many thanks to the good people at NUSMods for providing me with assistance along the way, such as their guidance on how to access student reviews via the Disqus API.")
st.markdown("Sadly, it turns out that the name \"NUSModerator\" [has actually been used before](https://github.com/nusmodifications/nusmods/tree/master/packages/nusmoderator). I guess I'm still hopeless when it comes to naming stuff - if I ever have children, may God bless them.")

# Display information section
st.markdown("### About Me")
st.markdown("Yo, I'm Bing Xuan. I'm currently a Year 3 Data Science and Analytics student at the National University of Singapore. Feel free to check out my [LinkedIn](https://www.linkedin.com/in/bing-xuan-chia/) and [GitHub](https://github.com/chiabingxuan)!")