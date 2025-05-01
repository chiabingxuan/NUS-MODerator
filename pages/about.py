from dotenv import load_dotenv
import os
import streamlit as st

load_dotenv()

# Display header
st.header("About")

# Display acknowledgements section
st.markdown("### Acknowledgements")
st.markdown("It turns out that the good people at NUSMods had actually [used the name \"NUSModerator\"](https://github.com/nusmodifications/nusmods/tree/master/packages/nusmoderator) before I ever did. I guess I'm still hopeless when it comes to naming stuff - if I ever have children, may God bless them.")

# Display information section
st.markdown("### About Me")
st.markdown("Yo, I'm Bing Xuan. I'm currently a Year 3 Data Science and Analytics student at the National University of Singapore. Feel free to check out my [LinkedIn](https://www.linkedin.com/in/bing-xuan-chia/) and [GitHub](https://github.com/chiabingxuan)!")