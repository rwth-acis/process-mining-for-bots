import sqlalchemy
import pandas as pd

# pip install dogpile.cache for caching the sql results
"""
This function reads the events from the database and returns a pandas dataframe
"""
def read_events_into_df(db_connection,start_date = None, end_date =None, resource_ids = None):
    if db_connection is None:
        raise ValueError('db_connection must be set')
    print('Reading events from database', start_date, end_date)
    if start_date is None or end_date is None:
        df = pd.read_sql('SELECT EVENT,CASE_ID,ACTIVITY_NAME, TIME_OF_EVENT, LIFECYCLE_PHASE, RESOURCE, RESOURCE_TYPE, REMARKS FROM MESSAGE WHERE CASE_ID IS NOT NULL AND RESOURCE IN %s', con=db_connection, params=(resource_ids))
    else:
        statement = 'SELECT EVENT,CASE_ID,ACTIVITY_NAME, TIME_OF_EVENT, LIFECYCLE_PHASE, RESOURCE, RESOURCE_TYPE, REMARKS FROM MESSAGE WHERE CASE_ID IS NOT NULL AND RESOURCE IN %s AND TIME_STAMP BETWEEN %s AND %s'
        # format the statement
        df = pd.read_sql(statement, con=db_connection, params=(resource_ids,start_date, end_date))
    # rename columns CASE_ID->case:concept:name, ACTIVITY_NAME->concept:name, TIME_OF_EVENT->time:timestamp, LIFECYCLE_PHASE->lifecycle:transition
    df.rename(columns={'CASE_ID': 'case:concept:name', 'ACTIVITY_NAME': 'concept:name', 'TIME_OF_EVENT': 'time:timestamp', 'LIFECYCLE_PHASE': 'lifecycle:transition'}, inplace=True)
    return df

def get_connection(host,port, user, password, db = 'LAS2PEERMON'):
    if(host is None or user is None or password is None):
        raise ValueError('mysql host, user and password must be set')
    db_connection = sqlalchemy.create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{db}')
    #test connection
    db_connection.connect()
    if db_connection is None:
        raise ValueError('Could not connect to database')
    return db_connection