from sqlalchemy import create_engine

def push_postgres(df,table,connection):
    engine = create_engine(connection)
    df.to_sql(table, engine,if_exists='replace',index=False)