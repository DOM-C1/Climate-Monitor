"""Create and host a streamlit dashboard"""

import streamlit as st


def intro():

    st.write("# Welcome to the Climate Monitor! :sun_small_cloud:")

    st.markdown(
        """
        
        This is a very fun and interesting description about this dashboard.

        **👈 Select a page from the menu on the left** to explore the dashboard!

        **Quick search**: Search the coming forecast and find weather alerts by location!

        **Explore**: Explore the current weather across the UK.

        ### Want to sign up to daily newsletters, or receive notifications about weather alerts near you?

        - Then check out [our website](https://random.org)!

        ### This project
        - Check out this climate monitor project on [GitHub](https://github.com/DOM-C1/Climate-Monitor)

        ### Contributors
        Project manager: **Dom Chambers**

        Quality Assurance: **Arjun Babhania**

        Architect: **Nathan McKittrick**

        Architect: **Dana Weetman**
    """
    )


if __name__ == "__main__":
    intro()
