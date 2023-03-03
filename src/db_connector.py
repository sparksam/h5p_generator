import psycopg2
import os
from legacy_objects import Answer, Exercise, PublicationGroup, Stem, StemAnswer
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


def load_exercises(connection, publication_id: int) -> Exercise:
    query = f"""SELECT {','.join(['e.id','e.title', 'e.stimulus', 'e.created_at', 'e.updated_at', 'e.context', 'p.id', 'p.uuid', 'p.publishable_type', 'p.version', 'p.license_id', 'pg.id', 'pg.uuid', 'pg.publishable_type', 'pg.number', 'pg.solutions_are_public', 'pg.nickname'])} from publications p inner join exercises e on e.id=p.publishable_id inner join publication_groups pg on pg.id=p.publication_group_id where p.id={publication_id} and p.publishable_type='Exercise';"""
    result = execute_query(connection=connection, query=query)[0]
    return Exercise(id=result[0], title=result[1], stimulus=result[2], created=result[3], updated=result[4], context=result[5], questions=[], publication_id=result[6], uuid=result[7], type=result[8], version=result[9], license=result[10], publication_group=PublicationGroup(id=result[11], uuid=result[12], type=result[13], number=result[14], is_solution_public=result[15], nickname=result[16]))


def load_exercises_ids(connection, limit: int) -> list[int]:
    return [r[0] for r in execute_query(connection=connection, query=f"""SELECT id from exercises LIMIT {limit};""")]


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

    ids = load_exercises_ids(connection=connection, limit=1000)
    print(load_exercises(connection=connection, publication_id=79004))

    # for i in ids:
    #     stems = [x for x in load_stem_question(
    #         connection=connection, config=config, exercise_id=i)]
    #     for s in stems:
    #         with open(f"generated/questions/question_{s.id}.json", "w") as outfile:
    #             outfile.write(str(s))
    #         with open(f"generated/h5p/content_{s.id}.json", "w") as outfile:
    #             outfile.write(json.dumps(s.generate_h5p(), indent=4))

    """ 
    - Storage of the generated H5P (Generated on fly??)
    - Metadata from the legacy system
    - Ways to store the new H5P files (Target, H5P tools or configure our own tools.)
    - Custom libraries?? 
    - Phil storage format, XML or JSON (Validation)
    
    """

    """ 
    - Users: Vendors and Content managers (Probably use Lumia)
    - Metadata from the DB. 
    - Official H5p Editor, Integration to Poet. (Exploration)
    - Database storage or Git. Could be unzipped and searched.
    - Store the metadata inside and ensure it is not lost by the H5P editor.
    - Multiple types of questions in one question. 
    - Content linking with the exercises. (More exploration for better understanding) ( Book -> Exercise -> Book)
    - Getting the H5p Editor running in VSCode and if it keeps metadata.
    """
