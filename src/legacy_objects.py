import json

class PublicationGroup:
    def __init__(self) -> None:
        self.id
        self.uuid
        self.type
        self.number


class Publication:
    def __init__(self) -> None:
        self.id
        self.uuid
        self.type
        self.version
        self.license
        self.created
        self.updated
        self.publication_group
        self.nickname
        self.public_solutions


class Exercise:
    def __init__(self, id, title, stimulus, created, updated, context, questions) -> None:
        self.id = id
        self.title = title
        self.stimulus = stimulus
        self.created = created
        self.updated = updated
        self.context = context
        self.questions = questions


class Question:
    def __init__(self, id, stimulus, created, updated, answer_order_matters, sort_position) -> None:
        self.id = id
        self.stimilus = stimulus
        self.created = created
        self.updated = updated
        self.answer_order_matters = answer_order_matters
        self.sort_position = sort_position
        self.answers = []


class Answer:
    def __init__(self, id, content, created, updated, sort_position) -> None:
        self.id = id
        self.content = content
        self.created = created
        self.updated = updated
        self.sort_position = sort_position


class Stem(Question):
    def __init__(self, id, content, stimulus, created, updated, answer_order_matters, sort_position) -> None:
        Question.__init__(self, id, stimulus, created,
                                       updated, answer_order_matters, sort_position)
        self.content = content
    def __str__(self) -> str:
        return json.dumps(self.__dict__,indent=4, sort_keys=False, default=str)


class StemAnswer(Answer):
    def __init__(self, id, content, created, updated, sort_position, correctness, feedback) -> None:
        Answer.__init__(self, id, content, created, updated, sort_position)
        self.correctness = correctness
        self.feedback = feedback
