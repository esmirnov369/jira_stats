from sqlalchemy import create_engine
import pandas as pd 
import numpy as np 



def push_postgres(df,table,connection):
    engine = create_engine(connection)
    query = text(f""" INSERT INTO jira VALUES {','.join([str(i) for i in list(df.to_records(index=False))])} ON CONFLICT ON CONSTRAINT issue_key DO NOTHING""")
    engine.connect().execute(query)
