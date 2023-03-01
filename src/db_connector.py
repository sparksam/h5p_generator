import psycopg2
import os
from legacy_objects import Answer, Stem, StemAnswer
import pathlib
import yaml
import json


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


def load_exercises_ids(connection, Limit: int) -> list[int]:
    return [r[0] for r in execute_query(connection=connection, query=f"""SELECT id from exercises LIMIT {Limit};""")]

def load_question(connection, table_name: str, fields: list, exercise_id: int) -> list[tuple]:
    query = f""" SELECT {','.join(fields) if len(fields)>0 else '*'} from {table_name} where id in (SELECT id from questions where exercise_id={exercise_id}); """
    return execute_query(connection=connection, query=query)


def load_stem(connection, table_name: str, fields: list, exercise_id: int) -> list[tuple]:
    query = f""" SELECT {','.join(fields) if len(fields)>0 else '*'} from {table_name} where question_id in (SELECT id from questions where exercise_id={exercise_id}); """
    return execute_query(connection=connection, query=query)

def load_answers(connection,  fields: list, question_id: id) -> list[tuple]:
    query = f""" SELECT {','.join(fields) if len(fields)>0 else '*'} from  answers where question_id={question_id}; """
    return execute_query(connection=connection, query=query)


def load_stem_answers(connection, fields: list, stem_id: id) -> list[tuple]:
    query = f""" SELECT {','.join(fields) if len(fields)>0 else '*'} from stem_answers where stem_id={stem_id}; """
    print(query)
    return execute_query(connection=connection, query=query)


def load_stem_question(connection, config, exercise_id: id) -> list[Stem]:
    results = list()
    questions = load_question(connection=connection, table_name="questions", fields=[
                              'stimulus', 'answer_order_matters', 'sort_position'], exercise_id=exercise_id)
    stems = load_stem(connection=connection, table_name="stems", fields=[
        'id', 'content', 'created_at', 'updated_at'], exercise_id=exercise_id)
    for q, s in zip(questions, stems):
        stem_answers = load_stem_answers(connection=connection, fields=[
                                         "correctness", "feedback"], stem_id=s[0])
        answer_results = load_answers(connection=connection, fields=[
            "id", "content", "created_at", "updated_at", "sort_position"], question_id=s[0])

        answers = [StemAnswer(id=a[0], content=a[1], created=a[2], updated=a[3], sort_position=a[4], correctness=sa[0], feedback=sa[1])
                   for a, sa in zip(answer_results, stem_answers)]

        stem = Stem(config=config, id=s[0], content=s[1], created=s[2], updated=s[3],
                    stimulus=q[0], answer_order_matters=q[1], sort_position=q[2], answers=answers)

        results.append(stem)
    return results

def init():
    env = pathlib.Path() / '.env'
    if env.exists():
        for line in env.read_text().split('\n'):
            if len(line):
                k, v = [s.strip() for s in line.split('=')]
                os.environ[k] = v


# TODO
# - Generate metadata files for the questions
# - Generate the H5P files from the database
# -
# - Generate for different type of questions.

# - Add Publications and publication groups
# - Consider the styles to generate the H5P files and type of questions. 
# - Solve the N/A problem for some answers

if __name__ == "__main__":
    init()
    connection = psycopg2.connect(host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
                                  database=os.getenv("DB_NAME"), user=os.getenv("DB_USERNAME"),
                                  password=os.getenv("DB_PASSWORD"))
    with open(os.sep.join(['configuration', 'lang', 'en.yaml']), 'r') as file:
        config = yaml.safe_load(file)
    assert config is not None
    # all_databases = list_databases(connection=connection)
    # all_tables = list_all_tables(connection=connection)

    # print (all_tables)

    ids = load_exercises_ids(connection=connection, Limit=1000)
    for i in ids:
        stems = [x for x in load_stem_question(
            connection=connection, config=config, exercise_id=i)]
        for s in stems:
            with open(f"generated/questions/question_{s.id}.json", "w") as outfile:
                outfile.write(str(s))
            with open(f"generated/h5p/content_{s.id}.json", "w") as outfile:
                outfile.write(json.dumps(s.generate_h5p(), indent=4))
