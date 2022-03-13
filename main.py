import pandas as pd
import streamlit as st
import tarfile
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Diagnostics")
st.markdown(
    """
    <style>
    .main {
    background-color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True
)

background_color = "#ffffff"


header = st.container()
col1, col3, col4 = st.columns([1,1,1])
drawcol1, drawcol2 = st.columns(2)
singlecol1, singlecol2 = st.columns(2)
duocol1, duocol2 = st.columns(2)
nanogridcol1, nanogridcol2 = st.columns(2)
Messagecol2, Messagecol4= st.columns(2)
messagecont = st.container()
gridcentralcol1, gridcentralcol2 = st.columns(2)
sidebar = st.container()
main = st.container()

dfAllData = None
dfMessages = None
dfDrawHome = None
dfSingle = None
dfSingleOld = None
dfLeft = None
dfRight = None
dfnanogrid = None
dfnanogridnode = None
tarnanogrid = None


with sidebar:
    st.sidebar.title("Selection:")

    st.sidebar.subheader("Select a .tgz ")
    file = st.sidebar.file_uploader("Fileselector", type="tgz")

    if not file == None:
        tar = tarfile.open(fileobj=file, mode="r:gz")
        tarmembers = tar.getnames()
        st.balloons()

        # -- Export specific files within the diagnostics
        tarmanager = tar.extractfile("./chargemanager.ini")
        tarjournal = tar.extractfile("./journal.json")
        tarplatform = tar.extractfile("./platform.conf")

        if "./nanogrid.ini" in tarmembers:
            tarnanogrid = tar.extractfile("./nanogrid.ini")
            tarnanogridnode = tar.extractfile("./nanogrid_node_config.ini")


# -- If file is selected - initiate dataframes. --#

        # -- Import chargemanager.ini as dfManager
        dfManager = pd.read_csv(tarmanager, delimiter="=", on_bad_lines='skip')
        dfManager.columns = ["Value"]
        CBID = dfManager.loc['chargeboxidentity']['Value']

        # -- Import platform.conf as dfPlatform
        dfPlatform = pd.read_csv(tarplatform, delimiter="=", on_bad_lines='skip', usecols=[0,1])
        dfPlatform.columns = ["Key", "Value"]
        dfPlatform.set_index('Key', inplace=True)
        modelversion = dfPlatform.loc['modelversion']['Value']
        model = dfPlatform.loc['model']['Value']
        mfgdate = dfPlatform.loc['mfgdate']['Value']

        # -- Import nanogrid and nanogridnode if they exist
        if tarnanogrid is not None:
            dfnanogrid = pd.read_csv(tarnanogrid, header=None)
            dfnanogridnode = pd.read_fwf(tarnanogridnode, header=None)

        # -- Import journal.json as dfAllData
        dfAllData = pd.io.json.read_json(tarjournal, lines=True)
        dfAllData['__REALTIME_TIMESTAMP'] = (pd.to_datetime(dfAllData['__REALTIME_TIMESTAMP'], unit='us'))
        dfAllData.rename(columns={'__REALTIME_TIMESTAMP': 'Time'}, inplace=True)
        dfAllData.rename(columns={'_HOSTNAME': 'CBID'}, inplace=True)
        dfAllData['CBID'] = dfAllData['CBID'].str.upper()
        # -- Separate 'Messages' and REALTIME_TIMESTAMP into own DF
        dfMessages = dfAllData[['Time', 'MESSAGE']].copy()
        pd.DataFrame(dfMessages)

        # -- Left outlet messages
        LeftOutlet = True
        LeftOutletCheck = dfMessages['MESSAGE'].str.startswith('[pwrctl.simple] _outletStatus "Left').values.tolist()

        if LeftOutlet in LeftOutletCheck:
            dfLeft = dfMessages.copy()
            pd.DataFrame(dfLeft)
            dfLeft = dfLeft[(dfLeft['MESSAGE'].str.startswith('[pwrctl.simple] _outletStatus "Left'))]
            dfLeftSplit = dfLeft['MESSAGE'].str.split(' ', n=-1, expand=True)
            dfLeft = dfLeft.drop(columns='MESSAGE')
            dfLeft = pd.merge(dfLeft, dfLeftSplit, left_index=True, right_index=True)

            dfLeft.rename(
                columns={
                    4: "PWM",
                    6: "Phases",
                    8: "Draw L1",
                    9: "Draw L2",
                    10: "Draw L3",
                    12: "State"
                }, inplace=True)
            dfLeft.drop(columns=[0, 1, 2, 3, 5, 7, 11], inplace=True)
            dfLeft[['PWM', 'Draw L1', 'Draw L2', 'Draw L3']] = dfLeft[
                ['PWM', 'Draw L1', 'Draw L2', 'Draw L3']].apply(
                pd.to_numeric)

        # -- Right outlet messages
        RightOutlet = True
        RightOutletCheck = dfMessages['MESSAGE'].str.startswith('[pwrctl.simple] _outletStatus "Right').values.tolist()

        if RightOutlet in RightOutletCheck:
            dfRight = dfMessages.copy()
            pd.DataFrame(dfRight)
            dfRight = dfRight[(dfRight['MESSAGE'].str.startswith('[pwrctl.simple] _outletStatus "Right'))]
            dfRightSplit = dfRight['MESSAGE'].str.split(' ', n=-1, expand=True)
            dfRight = dfRight.drop(columns='MESSAGE')
            dfRight = pd.merge(dfRight, dfRightSplit, left_index=True, right_index=True)

            dfRight.rename(
                columns={
                    4: "PWM",
                    6: "Phases",
                    8: "Draw L1",
                    9: "Draw L2",
                    10: "Draw L3",
                    12: "State"
                }, inplace=True)
            dfRight.drop(columns=[0, 1, 2, 3, 5, 7, 11], inplace=True)
            dfRight[['PWM', 'Draw L1', 'Draw L2', 'Draw L3']] = dfRight[
                ['PWM', 'Draw L1', 'Draw L2', 'Draw L3']].apply(
                pd.to_numeric)


        # -- Backend messages
        Backend = True
        BackendCheck = dfMessages['MESSAGE'].str.startswith('[ws.plain]').values.tolist()

        if Backend in BackendCheck:
            dfBackend = dfMessages.copy()
            pd.DataFrame(dfBackend)
            dfBackendNew = dfBackend[(dfBackend['MESSAGE'].str.startswith('[ws.plain]'))]
            dfBackend=dfBackendNew

        # -- ngHome - Initiated if message starts with [pwrctl.ng-home] _logTotalDraw totalDraw
        ngHome = True
        ngHomeCheck = dfMessages['MESSAGE'].str.startswith('[pwrctl.ng-home] _logTotalDraw totalDraw').values.tolist()

        if ngHome in ngHomeCheck:
            dfDrawHome = dfMessages.copy()
            pd.DataFrame(dfDrawHome)
            dfDrawHome = dfDrawHome[(dfDrawHome['MESSAGE'].str.startswith('[pwrctl.ng-home] _logTotalDraw totalDraw'))]

            dfDrawSplit = dfDrawHome['MESSAGE'].str.split(' ', n=-1, expand=True)
            dfDrawHome = dfDrawHome.drop(columns='MESSAGE')
            dfDrawHome = pd.merge(dfDrawHome, dfDrawSplit, left_index=True, right_index=True)
            dfDrawHome.rename(
                columns={
                    3: 'Draw L1',
                    4: 'Draw L2',
                    5: 'Draw L3',
                    7: 'Available L1',
                    8: 'Available L2',
                    9: 'Available L3'
                }, inplace=True)

            dfDrawHome.drop(columns=[0, 1, 2, 6], inplace=True)
            dfDrawHome[['Draw L1',
                        'Draw L2',
                        'Draw L3',
                        'Available L1',
                        'Available L2',
                        'Available L3']] = dfDrawHome[['Draw L1',
                                                       'Draw L2',
                                                       'Draw L3',
                                                       'Available L1',
                                                       'Available L2',
                                                       'Available L3']].apply(pd.to_numeric)

        # -- SingleOutlet -Initiated if message starts with [pwrctl.simple] _outletStatus "Single
        SingleOutlet = True
        SingleOutletCheck = dfMessages['MESSAGE'].str.startswith('[pwrctl.simple] _outletStatus "Single').values.tolist()

        if SingleOutlet in SingleOutletCheck:
            dfSingle = dfMessages.copy()
            pd.DataFrame(dfSingle)
            dfSingle = dfSingle[(dfSingle['MESSAGE'].str.startswith('[pwrctl.simple] _outletStatus "Single'))]
            dfSingleSplit = dfSingle['MESSAGE'].str.split(' ', n=-1, expand=True)
            dfSingle = dfSingle.drop(columns='MESSAGE')
            dfSingle = pd.merge(dfSingle, dfSingleSplit, left_index=True, right_index=True)

            dfSingle.rename(
                        columns={
                            4: "PWM",
                            6: "Phases",
                            8: "Draw L1",
                            9: "Draw L2",
                            10: "Draw L3",
                            12: "State"
                                }, inplace=True)
            dfSingle.drop(columns=[0, 1, 2, 3, 5, 7, 11], inplace=True)
            dfSingle[['PWM', 'Draw L1', 'Draw L2', 'Draw L3']] = dfSingle[
                ['PWM', 'Draw L1', 'Draw L2', 'Draw L3']].apply(pd.to_numeric)

        # -- SingleOutlet -Initiated if message starts with [pwrctl] _logOutletStatus "Single
        SingleOutletOld = True
        SingleOutletOldCheck = dfMessages['MESSAGE'].str.startswith('[pwrctl] _logOutletStatus "Single').values.tolist()

        if SingleOutletOld in SingleOutletOldCheck:
            dfSingleOld = dfMessages.copy()
            pd.DataFrame(dfSingleOld)
            dfSingleOld = dfSingleOld[(dfSingleOld['MESSAGE'].str.startswith('[pwrctl] _logOutletStatus "Single'))]
            dfSingleOldSplit = dfSingleOld['MESSAGE'].str.split(' ', n=-1, expand=True)
            dfSingleOld = dfSingleOld.drop(columns='MESSAGE')
            dfSingleOld = pd.merge(dfSingleOld, dfSingleOldSplit, left_index=True, right_index=True)
            dfSingleOld.rename(
                            columns={
                                4: "PWM",
                                6: "Phases",
                                8: "Draw L1",
                                9: "Draw L2",
                                10: "Draw L3",
                                12: "State"
                                    }, inplace=True)
            dfSingleOld.drop(columns=[0, 1, 2, 3, 5, 7, 11], inplace=True)
            dfSingleOld[['PWM', 'Draw L1', 'Draw L2', 'Draw L3']] = dfSingleOld[
                ['PWM', 'Draw L1', 'Draw L2', 'Draw L3']].apply(pd.to_numeric)

        gridcentral = True
        gridcentralcheck = dfMessages['MESSAGE'].str.startswith('[ng.fuse.aggregated]').values.tolist()

        if gridcentral in gridcentralcheck:
            dfgridcentral = dfMessages.copy()
            pd.DataFrame(dfgridcentral)
            dfgridcentral = dfgridcentral[(dfgridcentral['MESSAGE'].str.startswith('[ng.fuse.aggregated]'))].copy()
            dfgridcentralsplit = dfgridcentral['MESSAGE'].str.split(' ', n=-1, expand=True)
            dfgridcentral = dfgridcentral.drop(columns='MESSAGE')
            dfgridcentral = pd.merge(dfgridcentral, dfgridcentralsplit, left_index=True, right_index=True)
            dfgridcentral.rename(columns={
                                    3: "Draw L1",
                                    4: "Draw L2",
                                    5: "Draw L3",},
                                inplace=True)
            dfgridcentral.drop(columns=[0, 1, 2], inplace=True)
            dfgridcentral[['Draw L1', 'Draw L2', 'Draw L3']] = dfgridcentral[['Draw L1', 'Draw L2', 'Draw L3']].apply(pd.to_numeric)

        nanogridstation = True
        nanogridstationCheck = dfMessages['MESSAGE'].str.startswith('[ng.server.outlet]').values.tolist()

        if nanogridstation in nanogridstationCheck:
            dfnanogridstation = dfMessages.copy()

            pd.DataFrame(dfnanogridstation)
            dfnanogridstation = dfnanogridstation[
                (dfnanogridstation['MESSAGE'].str.startswith('[ng.server.outlet]'))].copy()
            dfnanogridstationSplit = dfnanogridstation['MESSAGE'].str.split(' ', n=-1, expand=True)

            dfnanogridstation = dfnanogridstation.drop(columns='MESSAGE')
            dfnanogridstation = pd.merge(dfnanogridstation, dfnanogridstationSplit, left_index=True, right_index=True)
            dfnanogridstation.rename(columns={
                0: "Message",
                1: "CBID",
                4: "Outlet",
                7: "Reserved A",
                11: "OutletStatus",
                12: "Phase"},
                inplace=True)
            dfnanogridstation.drop(columns='Message', inplace=True)
            dfnanogridstation.drop(columns=[2, 3, 5, 6, 8, 9, 10, 13, 14], inplace=True)

            dfnanogridstation['CBID'] = dfnanogridstation['CBID'].str.replace(r'"', "")
            ConnectedStations = dfnanogridstation.CBID.unique()

            figNanogridLine = go.Figure()
            dfnanogridstation[['Reserved A']] = dfnanogridstation[['Reserved A']].apply(pd.to_numeric)
            dfnanogridstation[['Time']] = dfnanogridstation[['Time']].apply(pd.to_datetime)
            dfnanototalload = dfnanogridstation[['Time', 'Reserved A']].copy()

            dfnanogridstation['CBID'] = dfnanogridstation['CBID'] + "_" + dfnanogridstation['Outlet']
            dfnanogridstation.drop(columns=['Outlet'], inplace=True)

            dfnanogridPhase = dfnanogridstation.groupby('Phase')
            dfnanogridL1 = dfnanogridPhase.get_group('"L1"')
            dfnanogridL2 = dfnanogridPhase.get_group('"L2"')
            dfnanogridL3 = dfnanogridPhase.get_group('"L3"')

            dfnanogridL1Reserved = dfnanogridL1.pivot(values=['Reserved A'], index=['Time'], columns=['CBID'])
            dfnanogridL2Reserved = dfnanogridL2.pivot(values=['Reserved A'], index=['Time'], columns=['CBID'])
            dfnanogridL3Reserved = dfnanogridL3.pivot(values=['Reserved A'], index=['Time'], columns=['CBID'])

            dfnanogridL1Reserved.interpolate(method='linear', axis=0, inplace=True)
            dfnanogridL2Reserved.interpolate(method='linear', axis=0, inplace=True)
            dfnanogridL3Reserved.interpolate(method='linear', axis=0, inplace=True)

            dfTotal = pd.DataFrame()
            dfTotal['L1'] = dfnanogridL1Reserved[list(dfnanogridL1Reserved.columns)].sum(axis=1).copy()
            dfTotal['L2'] = dfnanogridL2Reserved[list(dfnanogridL2Reserved.columns)].sum(axis=1).copy()
            dfTotal['L3'] = dfnanogridL3Reserved[list(dfnanogridL3Reserved.columns)].sum(axis=1).copy()
            dfTotal.interpolate(method='pad', axis=0, inplace=True)
            dfTotal.reset_index(inplace=True)

            dfnanogridL1Reserved = dfnanogridL1Reserved.stack(1)
            dfnanogridL2Reserved = dfnanogridL2Reserved.stack(1)
            dfnanogridL3Reserved = dfnanogridL3Reserved.stack(1)

            dfnanogridL1Reserved.reset_index(inplace=True)
            dfnanogridL2Reserved.reset_index(inplace=True)
            dfnanogridL3Reserved.reset_index(inplace=True)

            dfnanogridL1Reserved = dict(tuple(dfnanogridL1Reserved.groupby('CBID')))
            dfnanogridL2Reserved = dict(tuple(dfnanogridL2Reserved.groupby('CBID')))
            dfnanogridL3Reserved = dict(tuple(dfnanogridL3Reserved.groupby('CBID')))


            def displayreserved(X, Y):
                for i, X in X.items():
                    StationOutlet = X.iloc[0]['CBID']
                    figNanogridLine.add_trace(go.Scatter(x=X.Time, y=X['Reserved A'],
                                                         legendgrouptitle_text=Y,
                                                         legendgroup=Y,
                                                         mode='lines', name=StationOutlet,
                                                         line=dict(width=2)))
                figNanogridLine.update_layout(margin_l=0,
                                              margin_r=0,
                                              margin_t=60,
                                              margin_b=0,
                                              margin_pad=0,
                                              width=1900,
                                              height=450,
                                              plot_bgcolor="#f6f8fb")


            displayreserved(dfnanogridL1Reserved, 'L1')
            displayreserved(dfnanogridL2Reserved, 'L2')
            displayreserved(dfnanogridL3Reserved, 'L3')

            figNanogridLine.add_trace(go.Scatter(x=dfTotal.Time, y=dfTotal['L1'],
                                                 legendgrouptitle_text='TotalReserved',
                                                 legendgroup='TotalReserved',
                                                 mode='lines', name="L1-Total",
                                                 line=dict(width=2, color='#AA3F01'),
                                                 opacity=1, ))
            figNanogridLine.add_trace(go.Scatter(x=dfTotal.Time, y=dfTotal['L2'],
                                                 legendgrouptitle_text='TotalReserved',
                                                 legendgroup='TotalReserved',
                                                 mode='lines', name="L2-Total",
                                                 line=dict(width=2, color='#000000'),
                                                 opacity=1, ))
            figNanogridLine.add_trace(go.Scatter(x=dfTotal.Time, y=dfTotal['L3'],
                                                 legendgrouptitle_text='TotalReserved',
                                                 legendgroup='TotalReserved',
                                                 mode='lines', name="L3-Total",
                                                 line=dict(width=2, color='#A6A6A6'),
                                                 opacity=1, ))



# -- Visualize and structure of the data

        with header:
            st.title(CBID)
            st.write(model+" "+modelversion)
            st.write("Manufacturing date: "+mfgdate)

        if dfManager is not None:
            with col1:
                st.image("https://incharge.vattenfall.se/media/1869/eve-chargestorm.gif")
            with col3:
                st.subheader("Chargemanager")
                figManagerTable = go.Figure(data=[go.Table(
                    header=None,
                    cells=dict(values=[dfManager.index, dfManager['Value']],
                               fill_color="#f6f8fb",
                               align="left",
                               height=25),
                    columnwidth=[1, 1.5]
                )])
                figManagerTable.update_layout(
                    margin_l=0, margin_r=15, margin_t=0, margin_b=0, margin_pad=0,
                    width=600, height=500,
                    font_size=14)
                st.write(figManagerTable)

        if dfPlatform is not None:
            with col4:
                st.subheader("Platform")
                figPlatformTable = go.Figure(data=[go.Table(
                    header=None,
                    cells=dict(values=[dfPlatform.index, dfPlatform['Value']],
                               fill_color="#f6f8fb",
                               align="left",
                               height=25),
                    columnwidth=[1, 1.5]
                )])
                figPlatformTable.update_layout(
                    margin_l=0, margin_r=15, margin_t=0, margin_b=0, margin_pad=0,
                    width=600, height=500,
                    font_size=14)
                st.write(figPlatformTable)

        if dfDrawHome is not None:
            with drawcol1:
                if st.sidebar.checkbox("Home Nanogrid", value=True):
                    st.subheader("Home Nanogrid")
                    figDrawTable = go.Figure(data=[go.Table(
                        header=dict(values=list(dfDrawHome.columns),
                                    fill_color="#869bad",
                                    align="left"),
                        cells=dict(values=[dfDrawHome.Time,
                                           dfDrawHome['Draw L1'],
                                           dfDrawHome['Draw L2'],
                                           dfDrawHome['Draw L3'],
                                           dfDrawHome['Available L1'],
                                           dfDrawHome['Available L2'],
                                           dfDrawHome['Available L3']
                                           ],
                                   fill_color="#f6f8fb",
                                   align="left",
                                   height=25),
                        columnwidth=[1.7, 1, 1, 1, 1, 1, 1]
                        )])
                    figDrawTable.update_layout(
                        margin_l=0, margin_r=15, margin_t=0, margin_b=0, margin_pad=0,
                        width=900, height=400,
                        font_size=14)
                    st.write(figDrawTable)

                    with drawcol2:
                        figDrawLine = go.Figure()
                        figDrawLine.add_trace(go.Scatter(x=dfDrawHome.Time, y=dfDrawHome['Draw L1'],
                                                         mode='lines', name='Draw L1',
                                                         line=dict(color='#AA3F01', width=2)))
                        figDrawLine.add_trace(go.Scatter(x=dfDrawHome.Time, y=dfDrawHome['Draw L2'],
                                                         mode='lines', name='Draw L2',
                                                         line=dict(color='#000000', width=2)))
                        figDrawLine.add_trace(go.Scatter(x=dfDrawHome.Time, y=dfDrawHome['Draw L3'],
                                                         mode='lines', name='Draw L3',
                                                         line=dict(color='#A6A6A6', width=2)))
                        figDrawLine.update_layout(margin_l=0,
                                                  margin_r=0,
                                                  margin_t=60,
                                                  margin_b=0,
                                                  margin_pad=0,
                                                  width=900,
                                                  height=450,
                                                  plot_bgcolor="#f6f8fb")

                        st.write(figDrawLine)


        if dfSingle is not None:
            with singlecol1:
                if st.sidebar.checkbox("Single Outlet", value=True):
                    st.subheader("Single Outlet")
                    figSingleTable = go.Figure(data=[go.Table(
                        header=dict(values=list(dfSingle.columns),
                                    fill_color="#869bad",
                                    align="left"),
                        cells=dict(values=[dfSingle.Time,
                                           dfSingle['PWM'],
                                           dfSingle['Phases'],
                                           dfSingle['Draw L1'],
                                           dfSingle['Draw L2'],
                                           dfSingle['Draw L3'],
                                           dfSingle['State'],
                                           ],
                                   fill_color="#f6f8fb",
                                   align="left",
                                   height=25),
                        columnwidth=[1.5, 0.5, 0.5, 1, 1, 1, 1]
                    )])
                    figSingleTable.update_layout(
                        margin_l=0, margin_r=15, margin_t=0, margin_b=0, margin_pad=0,
                        width=900, height=400,
                        font_size=14)
                    st.write(figSingleTable)

                    with singlecol2:
                        figSingleLine = go.Figure()
                        figSingleLine.add_trace(go.Scatter(x=dfSingle.Time, y=dfSingle['PWM'],
                                                           mode='lines', name='PWM',
                                                           line=dict(color='#0400FF', width=2)))
                        figSingleLine.add_trace(go.Scatter(x=dfSingle.Time, y=dfSingle['Draw L1'],
                                                         mode='lines', name='Draw L1',
                                                         line=dict(color='#AA3F01', width=2)))
                        figSingleLine.add_trace(go.Scatter(x=dfSingle.Time, y=dfSingle['Draw L2'],
                                                         mode='lines', name='Draw L2',
                                                         line=dict(color='#000000', width=2)))
                        figSingleLine.add_trace(go.Scatter(x=dfSingle.Time, y=dfSingle['Draw L3'],
                                                         mode='lines', name='Draw L3',
                                                         line=dict(color='#A6A6A6', width=2)))

                        figSingleLine.update_layout(margin_l=0,
                                                  margin_r=0,
                                                  margin_t=60,
                                                  margin_b=0,
                                                  margin_pad=0,
                                                  width=900,
                                                  height=450,
                                                  plot_bgcolor="#f6f8fb")

                        st.write(figSingleLine)

        if dfSingleOld is not None:
            with singlecol1:
                if st.sidebar.checkbox("Single Outlet", value=True):
                    st.subheader("Single Outlet")
                    figSingleTable = go.Figure(data=[go.Table(
                        header=dict(values=list(dfSingleOld.columns),
                                    fill_color="#869bad",
                                    align="left"),
                        cells=dict(values=[dfSingleOld.Time,
                                           dfSingleOld['PWM'],
                                           dfSingleOld['Phases'],
                                           dfSingleOld['Draw L1'],
                                           dfSingleOld['Draw L2'],
                                           dfSingleOld['Draw L3'],
                                           dfSingleOld['State'],
                                           ],
                                   fill_color="#f6f8fb",
                                   align="left",
                                   height=25),
                        columnwidth=[1.5, 0.5, 0.5, 1, 1, 1, 1]
                    )])
                    figSingleTable.update_layout(
                        margin_l=0, margin_r=15, margin_t=0, margin_b=0, margin_pad=0,
                        width=900, height=400,
                        font_size=14)
                    st.write(figSingleTable)

                    with singlecol2:
                        figSingleLine = go.Figure()
                        figSingleLine.add_trace(go.Scatter(x=dfSingleOld.Time, y=dfSingleOld['PWM'],
                                                           mode='lines', name='PWM',
                                                           line=dict(color='#0400FF', width=2)))
                        figSingleLine.add_trace(go.Scatter(x=dfSingleOld.Time, y=dfSingleOld['Draw L1'],
                                                           mode='lines', name='Draw L1',
                                                           line=dict(color='#AA3F01', width=2)))
                        figSingleLine.add_trace(go.Scatter(x=dfSingleOld.Time, y=dfSingleOld['Draw L2'],
                                                           mode='lines', name='Draw L2',
                                                           line=dict(color='#000000', width=2)))
                        figSingleLine.add_trace(go.Scatter(x=dfSingleOld.Time, y=dfSingleOld['Draw L3'],
                                                           mode='lines', name='Draw L3',
                                                           line=dict(color='#A6A6A6', width=2)))

                        figSingleLine.update_layout(margin_l=0,
                                                    margin_r=0,
                                                    margin_t=60,
                                                    margin_b=0,
                                                    margin_pad=0,
                                                    width=900,
                                                    height=450,
                                                    plot_bgcolor="#f6f8fb")

                        st.write(figSingleLine)

        if dfLeft is not None:
            with singlecol1:
                if st.sidebar.checkbox("Left Outlet", value=True):
                    st.subheader("Left Outlet")

                    figLeftTable = go.Figure(data=[go.Table(
                        header=dict(values=list(dfLeft.columns),
                                    fill_color="#869bad",
                                    align="left"),
                        cells=dict(values=[dfLeft.Time,
                                           dfLeft['PWM'],
                                           dfLeft['Phases'],
                                           dfLeft['Draw L1'],
                                           dfLeft['Draw L2'],
                                           dfLeft['Draw L3'],
                                           dfLeft['State'],
                                           ],
                                   fill_color="#f6f8fb",
                                   align="left",
                                   height=25),
                        columnwidth=[1.5, 0.5, 0.5, 1, 1, 1, 1]
                    )])
                    figLeftTable.update_layout(
                        margin_l=0, margin_r=15, margin_t=0, margin_b=0, margin_pad=0,
                        width=900, height=400,
                        font_size=14)
                    st.write(figLeftTable)

                    with singlecol2:
                        figLeftLine = go.Figure()
                        figLeftLine.add_trace(go.Scatter(x=dfLeft.Time, y=dfLeft['PWM'],
                                                           mode='lines', name='PWM',
                                                           line=dict(color='#0400FF', width=2)))
                        figLeftLine.add_trace(go.Scatter(x=dfLeft.Time, y=dfLeft['Draw L1'],
                                                           mode='lines', name='Draw L1',
                                                           line=dict(color='#AA3F01', width=2)))
                        figLeftLine.add_trace(go.Scatter(x=dfLeft.Time, y=dfLeft['Draw L2'],
                                                           mode='lines', name='Draw L2',
                                                           line=dict(color='#000000', width=2)))
                        figLeftLine.add_trace(go.Scatter(x=dfLeft.Time, y=dfLeft['Draw L3'],
                                                           mode='lines', name='Draw L3',
                                                           line=dict(color='#A6A6A6', width=2)))

                        figLeftLine.update_layout(margin_l=0,
                                                    margin_r=0,
                                                    margin_t=60,
                                                    margin_b=0,
                                                    margin_pad=0,
                                                    width=900,
                                                    height=450,
                                                    plot_bgcolor="#f6f8fb")
                        st.write(figLeftLine)

        if dfRight is not None:
            with duocol1:
                if st.sidebar.checkbox("Right Outlet", value=True):
                    st.subheader("Right Outlet")
                    figRightTable = go.Figure(data=[go.Table(
                        header=dict(values=list(dfRight.columns),
                                    fill_color="#869bad",
                                    align="left"),
                        cells=dict(values=[dfRight.Time,
                                           dfRight['PWM'],
                                           dfRight['Phases'],
                                           dfRight['Draw L1'],
                                           dfRight['Draw L2'],
                                           dfRight['Draw L3'],
                                           dfRight['State'],
                                           ],
                                   fill_color="#f6f8fb",
                                   align="left",
                                   height=25),
                        columnwidth=[1.5,0.5,0.5,1,1,1,1]
                    )])
                    figRightTable.update_layout(
                        margin_l=0, margin_r=15, margin_t=0, margin_b=0, margin_pad=0,
                        width=900, height=400,
                        font_size=14)
                    st.write(figRightTable)

                    with duocol2:
                        figRightLine = go.Figure()
                        figRightLine.add_trace(go.Scatter(x=dfRight.Time, y=dfRight['PWM'],
                                                         mode='lines', name='PWM',
                                                         line=dict(color='#0400FF', width=2)))
                        figRightLine.add_trace(go.Scatter(x=dfRight.Time, y=dfRight['Draw L1'],
                                                         mode='lines', name='Draw L1',
                                                         line=dict(color='#AA3F01', width=2)))
                        figRightLine.add_trace(go.Scatter(x=dfRight.Time, y=dfRight['Draw L2'],
                                                         mode='lines', name='Draw L2',
                                                         line=dict(color='#000000', width=2)))
                        figRightLine.add_trace(go.Scatter(x=dfRight.Time, y=dfRight['Draw L3'],
                                                         mode='lines', name='Draw L3',
                                                         line=dict(color='#A6A6A6', width=2)))

                        figRightLine.update_layout(margin_l=0,
                                                  margin_r=0,
                                                  margin_t=60,
                                                  margin_b=0,
                                                  margin_pad=0,
                                                  width=900,
                                                  height=450,
                                                  plot_bgcolor="#f6f8fb")
                        st.write(figRightLine)

        if dfnanogrid is not None:
            with nanogridcol1:
                if st.sidebar.checkbox("Nanogrid", value=True):
                    st.subheader("Nanogrid")
                    figNanogrid = go.Figure(data=[go.Table(
                        header=None,
                        cells=dict(values=[dfnanogrid],
                                   fill_color="#f6f8fb",
                                   align="left",
                                   height=25),
                        columnwidth=[1, 1])])
                    figNanogrid.update_layout(
                        margin_l=0, margin_r=15, margin_t=0, margin_b=0, margin_pad=0,
                        width=1000, height=800,
                        font_size=14)
                    st.write(figNanogrid)

                    with nanogridcol2:
                        st.subheader("Nanogrid-Node")
                        figNanogridnode = go.Figure(data=[go.Table(
                            header=None,
                            cells=dict(values=[dfnanogridnode],
                                       fill_color="#f6f8fb",
                                       align="left",
                                       height=25),
                            columnwidth=[1, 1])])
                        figNanogridnode.update_layout(
                            margin_l=0, margin_r=15, margin_t=0, margin_b=0, margin_pad=0,
                            width=1000, height=800,
                            font_size=14)
                        st.write(figNanogridnode)
            if st.sidebar.checkbox("Nanogrid Allocated", value=True):
                st.subheader('Nanogrid Allocated')
                st.write(figNanogridLine)

            if st.sidebar.checkbox("Gridcentral Measured Load", value=True):
                with gridcentralcol2:
                    figGridcentralLine = go.Figure()
                    figGridcentralLine.add_trace(go.Scatter(x=dfgridcentral.Time, y=dfgridcentral['Draw L1'],
                                                 mode='lines', name='Draw L1',
                                                 line=dict(color='#AA3F01', width=2)))
                    figGridcentralLine.add_trace(go.Scatter(x=dfgridcentral.Time, y=dfgridcentral['Draw L2'],
                                                 mode='lines', name='Draw L2',
                                                 line=dict(color='#000000', width=2)))
                    figGridcentralLine.add_trace(go.Scatter(x=dfgridcentral.Time, y=dfgridcentral['Draw L3'],
                                                 mode='lines', name='Draw L3',
                                                 line=dict(color='#A6A6A6', width=2)))
                    figGridcentralLine.update_layout(margin_l=0,
                                          margin_r=0,
                                          margin_t=60,
                                          margin_b=0,
                                          margin_pad=0,
                                          width=900,
                                          height=450,
                                          plot_bgcolor="#f6f8fb")

                    st.write(figGridcentralLine)
                with gridcentralcol1:
                    st.subheader("Gridcentral Measured Load")
                    figGridcentralTable = go.Figure(data=[go.Table(
                        header=dict(values=list(dfgridcentral.columns),
                                    fill_color="#869bad",
                                    align="left"),
                        cells=dict(values=[dfgridcentral.Time,
                                           dfgridcentral['Draw L1'],
                                           dfgridcentral['Draw L2'],
                                           dfgridcentral['Draw L3']
                                           ],
                                   fill_color="#f6f8fb",
                                   align="left",
                                   height=25),
                        columnwidth=[1, 1, 1, 1]
                    )])
                    figGridcentralTable.update_layout(
                        margin_l=0, margin_r=15, margin_t=0, margin_b=0, margin_pad=0,
                        width=900, height=400,
                        font_size=14)
                    st.write(figGridcentralTable)

        if dfMessages is not None:

            BackendButton = st.sidebar.checkbox("Backend Messages", value=False)
            MessageButton = st.sidebar.checkbox("All messages in Journal", value=False)

            def Backendfigure(x, y):
                st.subheader("Backend Messages")
                figBackend = go.Figure(data=[go.Table(
                    header=dict(values=list(dfBackend.columns),
                            fill_color="#869bad",
                            align="left"),
                    cells=dict(values=[dfBackend.Time, dfBackend.MESSAGE],
                            fill_color="#f6f8fb",
                            align="left",
                            height=25),
                            columnwidth=[1, y])])
                figBackend.update_layout(
                    margin_l=0, margin_r=15, margin_t=0, margin_b=0, margin_pad=0,
                    width=x, height=800,
                    font_size=14)
                st.write(figBackend)

            def Messagefigure(x, y):
                st.subheader("All messages in Journal")
                figMessages = go.Figure(data=[go.Table(
                    header=dict(values=list(dfMessages.columns),
                                fill_color="#869bad",
                                align="left"),
                    cells=dict(values=[dfMessages.Time, dfMessages.MESSAGE],
                                fill_color="#f6f8fb",
                                align="left",
                                height=25),
                                columnwidth=[1, y])])
                figMessages.update_layout(
                    margin_l=0, margin_r=15, margin_t=0, margin_b=0,margin_pad=0,
                    width=x, height=800,
                    font_size=14)
                st.write(figMessages)

            if BackendButton + MessageButton == 2:
                with Messagecol2:
                    Backendfigure(1000, 4)
                with Messagecol4:
                    Messagefigure(1000, 4)

            elif BackendButton + MessageButton == 1:
                if BackendButton == 1:
                    with messagecont:
                        Backendfigure(2000, 8)

                elif MessageButton == 1:
                    with messagecont:
                        Messagefigure(2000, 8)

    else:
        st.title("No file selected - Select a file in sidebar")
        st.sidebar.write("No file selected")

