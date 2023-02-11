import psycopg2
import os
from legacy_objects import Question, Stem
import pathlib


def execute_query(connection, query: str) -> list[tuple]:
    cursor = connection.cursor()
    cursor.execute(query=query)
    return cursor.fetchall()


def list_all_tables(connection):
    return execute_query(connection=connection, query="""  SELECT table_name
                        FROM information_schema.tables
                        ORDER BY table_name;
                """)


def list_databases(connection):
    return execute_query(connection=connection, query="""SELECT datname FROM pg_database WHERE datistemplate = false;""")


def load_question(connection, table_name: str, fields: list, exercise_id: int) -> list[tuple]:
    query = f""" SELECT {','.join(fields)} from {table_name} where id in (SELECT id from questions where exercise_id={exercise_id}); """
    print(query)
    return execute_query(connection=connection, query=query)


def load_stem_question(connection, exercise_id: id) -> list[Stem]:
    questions = load_question(connection=connection, table_name="questions", fields=[
                              'stimulus', 'answer_order_matters', 'sort_position'], exercise_id=exercise_id)
    print(questions)
    stems = load_question(connection=connection, table_name="stems", fields=[
        'id', 'content', 'created_at', 'updated_at'], exercise_id=exercise_id)
    return [Stem(id=x[0], content=x[1], created=x[2], updated=x[3], stimulus=y[0], answer_order_matters=y[1], sort_position=y[2]) for x, y in zip(stems, questions)]


def init():
    env = pathlib.Path() / '.env'
    if env.exists():
        for line in env.read_text().split('\n'):
            if len(line):
                k, v = [s.strip() for s in line.split('=')]
                os.environ[k] = v


if __name__ == "__main__":
    init()
    connection = psycopg2.connect(host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
                                  database=os.getenv("DB_NAME"), user=os.getenv("DB_USERNAME"),
                                  password=os.getenv("DB_PASSWORD"))
    # all_databases = list_databases(connection=connection)
    # all_tables = list_all_tables(connection=connection)

    # print (all_tables)
    stems = [str(x) for x in load_stem_question(
        connection=connection, exercise_id=31730)]
    print(stems[0])
