################# Setting up environment and fetching data from Google Sheets #################
import streamlit as st
import pandas as pd
import bcrypt
import re
import gspread
from streamlit_gsheets import GSheetsConnection
st.set_page_config(
            page_title="Sheets",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="collapsed",
        )
hash_password = st.secrets["app_credentials"]["hashed_password"]
def check_credentials(password):
    entered_password_bytes = password.encode('utf-8')
    correct_password_hash_bytes = hash_password.encode('utf-8')
    return bcrypt.checkpw(entered_password_bytes, correct_password_hash_bytes)
# --- Initialize session state ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'login_error' not in st.session_state:
    st.session_state.login_error = False
###############################Show login form if not logged in##########################################
if not st.session_state.logged_in:
    st.title("Login")

    with st.form("login_form"):
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

        if login_button:
            if check_credentials(password):
                st.session_state.logged_in = True
                st.session_state.login_error = False
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.session_state.login_error = True
                st.error("Invalid  password.")
                st.rerun()

    if st.session_state.login_error:
        st.warning("Please try again.")
################################Show main interface if logged in##########################################
else:
    with st.spinner("Connecting to Google Sheets..."):
        #scope = [ 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive' ]      
        service_account_info = st.secrets["gcp_service_account"]
        #client = gspread.service_account_from_dict(dict(service_account_info))
        from pathlib import Path
        client = gspread.service_account(filename=Path('.streamlit/ravits-lab-paraffin-blocks-e254d6aa1b19.json')) # type: ignore
        sheet = client.open("Ravits Lab Paraffin Blocks Inventory")
        sheet_guide = sheet.get_worksheet(0)
        sheet_summary=sheet.get_worksheet(1)
        sheet_detail= sheet.get_worksheet(2)
        conn = st.connection("ffpe_gsheets", type=GSheetsConnection)
    ################################## Initializing global funcs and  pre-processing data  ############################################

    def block_color_style(val):
        val_lower = val.lower() if isinstance(val, str) else ''
        background_color = ''  # Default value
        text_color = ''        # Default value
        if val_lower == "red":
            background_color = 'background-color: #da0000'
        elif val_lower == 'orange':
            background_color = 'background-color: #ff9966'
            text_color = 'color: #000'
        elif val_lower == 'gold':
            background_color = 'background-color: #fbc315'
            text_color = 'color: #000'
        elif val_lower == 'yellow':
            background_color = 'background-color: #faf28a'
            text_color = 'color: #000'
        elif val_lower == 'green':
            background_color = 'background-color: #99d3a1'
            text_color = 'color: #000'
        elif val_lower == "teal":
            background_color = 'background-color: #53ada3'
            text_color = 'color: #000'
        elif val_lower == "blue":
            background_color = 'background-color: #afcae7'
            text_color = 'color: #000'
        elif val_lower == "purple":
            background_color = 'background-color: #e78dd5'
            text_color = 'color: #000'
        elif val_lower == "pink":
            background_color = 'background-color: #f6cad9'
            text_color = 'color: #000'
        elif val_lower == "gray":
            background_color = 'background-color: #bdbdbd'
            text_color = 'color: #000'
        elif val_lower == "white":
            background_color = 'background-color: #FFFFFF'
            text_color = 'color: #000'
        return f"{background_color}; {text_color if 'text_color' in locals() else ''}"

    def block_status_style(val):
        val_lower = val.lower() if isinstance(val, str) else ''
        text_color=''
        background_color=''
        if val_lower=="uncut":
            background_color='background-color: #bdbdbd'
            text_color='color: #303030'
        elif val_lower=='cut':
            background_color='background-color: #009900'
            text_color='color: #FFF'
        elif val_lower=='low':
            background_color='background-color: #ffcc1e'
        elif val_lower=='used up':
            background_color='background-color: #da0000'
            text_color='color: #FFF'
        return f"{background_color}; {text_color}"
    
    def case_info_display(row):
        st.write(f"**Pt. {row.Case}**")
        st.write(f"**Primary Dx**: {row.Diagnosis}")
        st.write("Genetics:")
        st.write("Clinical Subtype:")
        st.write("Onset:")
    
    # preparing all data from the Google Sheets document
    full_list_of_lists = sheet_detail.get_all_values()[1:] #get all values from 'block details' sheet, remove header row ([0])
    mainDataDF = pd.DataFrame(full_list_of_lists, columns=sheet_detail.row_values(1),index=None) #manually assign header values from Gsheet

    diagnosis_index=[row[:2] for row in sheet_summary.get_all_values()[3:]]  # get diagnosis information from 'summary' sheet and Extract only the first two columns
    diagnosis_df = pd.DataFrame(diagnosis_index, columns=['Case', 'Diagnosis']) # Convert the list of lists to a DataFrame
    mainDataDF = pd.merge(mainDataDF, diagnosis_df, left_on='Case No.', right_on='Case', how='left') #merge the diagnosis information with the main data
    mainDataDF.drop(columns=['Case'], inplace=True) #remove duplicate 'Case' column
    mainDataDF.dropna(axis=0,subset='Diagnosis',inplace=True,) #remove rows with no Case No.
    activeBlocks = mainDataDF[mainDataDF['Active?']=="TRUE"]  

    ########################################### Actual interface begins here ####################################################

    padL,center, padR = st.columns([1, 3, 1])
    with center:
        st.markdown('''
            # :brain: Ravits Lab FFPE Blocks Inventory  
            :blue-badge[🚧The database is still not complete. Some blocks have not been logged yet.] ''')
    st.divider()    
    c1,c2,c3,c4=st.columns([4,1, 1, 1])
    c1.markdown('''
        Web application for accessing the paraffin blocks inventory. All data here is pulled from the Google Sheets document.    
        Please use the filter set below to crearte a list of blocks to include in an experiment.

        ''')
    c2.metric(label="Total Blocks", value=len(mainDataDF), help="Total number of FFPE blocks in the inventory.",border=True)
    c3.metric(label="Total Cases", value=len(mainDataDF['Case No.'].unique()), help="Number of cases that have blocks the inventory.",border=True)
    c4.metric(label="Active Blocks", value=len(activeBlocks), help="Number of blocks that are removed from the inventory to be used in an experiment.",border=True)
    @st.fragment
    def criteria_filter_main():
        
        def filter_diagnosis(arg: list):
            if not arg or "All" in arg:
                # No filtering, include all rows
                return mainDataDF['Diagnosis'].notna()
            pattern = []
            if "Control" in arg:
                pattern.append(r'control')
            if "sALS" in arg:
                pattern.append(r'sALS')
            if "fALS" in arg:
                pattern.append(r'fALS')
            regex = '|'.join(pattern)
            # Return a boolean Series for filtering
            return mainDataDF['Diagnosis'].astype(str).str.contains(regex, case=False, regex=True,na=False)
            
        def filter_region(arg: list):
            condition = []
            noMatch_flag = True
                #condition= mainDataDF['Block name'].notna()  # Return a Series of True for all rows
            if  any(re.search('[L,l]umb',item)for item in arg):
                noMatch_flag=False
                condition.append(r'[L,l]umb')
            if  any(re.search('[T,t]hor',item)for item in arg):
                noMatch_flag=False
                condition.append(r'[T,t]hor')        
            if  any(re.search('[C,c]erv',item)for item in arg):
                noMatch_flag=False
                condition.append(r'[C,c]erv')
            if any(re.search('[Mm][Cc]',item)for item in arg):
                noMatch_flag=False
                condition.append(r'[Mm][Cc]|[Mm]otor.*[Cc].*[Tt].*[Xx]|^[RL]G.*')
            if noMatch_flag:
                condition= mainDataDF['Block name'].notna()
                errorMsgContainer.markdown(f":red-badge[Filter '{arg}' is invalid or hasn't been implemented yet. Displaying all blocks.]")
                return condition
            else:
                regex = '|'.join(condition)
            return  mainDataDF['Block name'].astype(str).str.contains(regex, case=False, regex=True,na=False)    
        
        
        st.markdown(''' ## Filters ''')
        #display the input fields, and generate filters for each category based on the input
            
        with st.form(key="filter_lookup_input"):

            col1, col2 = st.columns([1, 1])
            # Diagnosis filter
            with col1:
                diag_list= st.multiselect(
                "Diagnosis",
                options=["Control", "sALS", "fALS"],
                default=["Control", "sALS", "fALS"],  # Default to all options selected
                )  

            # Anatomical Region filter  
            with col2:
                region_list=st.multiselect(
                    "Anatomical Region",
                    options=["Lumbar", "Thoracic", "Cervical", "MC"],
                    accept_new_options=True,
                    default=None,   
                )
                errorMsgContainer= st.empty()
                
            st.form_submit_button('Confirm')
        
        filter_combined = filter_diagnosis(diag_list) & filter_region(region_list) # Combine filters

        st.markdown(''' ## Blocks List ''')

        filtered_data = mainDataDF[filter_combined]
        filtered_data_color = filtered_data.style\
            .map(block_color_style, subset=['Block color'])\
            .map(block_status_style, subset=['Block status'])
   
        if len(filtered_data) == 0:
            st.markdown(f":red-badge[No blocks found for the selected filters.]")
        else:
            st.markdown(f":green-badge[Found {len(filtered_data)} blocks.]")
            #st.download_button(
            #    "Download List",
            #    data=filtered_data.to_csv(index=False).encode('utf-8'),
            #    on_click="ignore",
            #    key="dl_1")
        st.dataframe(
            filtered_data_color,
            column_order=[
                'Diagnosis','Block name', 'Case No.', 'Location', 'Block color', 'Block status','Notes'
            ],
            height=1000,
            hide_index=True,
            on_select="ignore",
            selection_mode='multi-row',
        )

    @st.fragment
    def case_filter_main():
        caseC1, caseC2 = st.columns([1, 3])   
        with caseC1: 
            st.markdown(''' ## Filter ''')
            with st.form(key="case_no_lookup_input"):
                caseNo_list=st.multiselect(
                    "Case Numbers",
                    options=diagnosis_df['Case'].unique(),
                    default=None
                )

                st.form_submit_button('Confirm')
            st.markdown('''## Case Info''')
            if caseNo_list:
                for _, row in diagnosis_df[diagnosis_df['Case'].isin(caseNo_list)].iterrows():
                     with st.container(border=True):
                        case_info_display(row)

            else:
                    st.markdown(":red-badge[Please select at least one Case No.]")    
        with caseC2:
            st.markdown(''' ## Blocks List ''')
            filtered_data = pd.DataFrame(mainDataDF[mainDataDF['Case No.'].isin(caseNo_list)])
            DLButton_Container = st.empty()
            if len(filtered_data) == 0:
                st.markdown(f":red-badge[No blocks found for Case No. {caseNo_list}]")
            else:
                st.markdown(f":green-badge[Found {len(filtered_data)} blocks for Case No. {caseNo_list}]")
            with st.expander("Fold/Unfold list", expanded=True):
                filtered_data_style = filtered_data.style\
                    .map(block_color_style, subset=['Block color'])\
                    .map(block_status_style, subset=['Block status'])
                
                st.dataframe(
                    filtered_data_style,
                    column_order=[
                        'Diagnosis','Block name', 'Case No.', 'Location', 'Block color', 'Block status','Notes'
                    ],
                    height=1000,
                    hide_index=True,
                    #on_select="rerun",
                    #selection_mode='multi-row',
                )
            #DLButton_Container.download_button(
            #    "Download List",
            #    data=filtered_data.to_csv(index=False).encode('utf-8'),
            #    on_click="ignore",
            #    key="dl_2")

    criterial_filter_tab, case_filter_tab =st.tabs(["Searcg by Criteria", "Look Up Cases"])

    with criterial_filter_tab:
        criteria_filter_main()
    with case_filter_tab:
        case_filter_main()

st.divider()
st.write("Please contact Alex Meng s7meng@health.ucsd.edu for any questions.")