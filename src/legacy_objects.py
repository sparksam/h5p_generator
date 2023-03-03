from functools import reduce
import json
import operator as op

MULTIPLE_CHOICE = 'multiple-choice'
MULTIPLE_SELECT = 'multiple-select'
SHORT_ANSWER = 'short-answer'
FILL_IN_THE_BLANK = 'fill-in-the-blank'
FREE_RESPONSE = 'free-response'
TRUE_FALSE = 'true-false'


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


class H5PExercise:
    def __init__(self, config: any = None) -> None:
        assert config is not None
        self.config = config

    def json_skip(self):
        return ["config"]

    def __str__(self) -> str:
        obj = self.__dict__.copy()
        for path in self.json_skip():
            path = path.split('/')
            del reduce(op.getitem, path[:-1], obj)[path[-1]]
        return json.dumps(obj, indent=4, sort_keys=False, default=lambda o: o.__dict__ if isinstance(o, Answer) else str(o))

    def generate_config_from_key(self, yaml_config_prefix: str):
        config_path = yaml_config_prefix.split('.')
        dialog_config = reduce(
            op.getitem, config_path[:-1], self.config)[config_path[-1]]
        generated_config = {}
        for key in dialog_config.keys():
            generated_config[key] = dialog_config[key]
        return generated_config

    def generate_confirm_check(self):
        return self.generate_config_from_key("dialogs.confirmCheck")

    def generate_retry_check(self):
        return self.generate_config_from_key("dialogs.confirmRetry")

    def generate_l10n(self):
        return self.generate_config_from_key("l10n")

    def generate_retry_behavior(self, library: str, args=None):
        default_behaviour = self.generate_config_from_key(library)
        if args is not None:
            for key in args.keys():
                default_behaviour[key] = args[key]
        return default_behaviour

    def generate_metadata_file(self):
        pass

    def generate_question(self):
        raise NotImplementedError("generate_question not implemented")

    def generate_answers(self):
        raise NotImplementedError("generate_question not implemented")

    def question_type(self):
        raise NotImplementedError("generate_question not implemented")

    def find_library(self):
        if self.question_type() == MULTIPLE_CHOICE:
            return "MultipleChoice"
        else:
            return None

    def generate_h5p(self):
        library = self.find_library()
        if library == "MultipleChoice":
            key = library[0].lower()+library[1:]
            result = self.generate_config_from_key(key)
            result["question"] = self.generate_question()
            result["answers"] = self.generate_answers()
            return result
        return None


class Question(H5PExercise):
    def __init__(self, config: any, id, stimulus, created, updated, answer_order_matters, sort_position, answers) -> None:
        H5PExercise.__init__(self, config)
        self.id = id
        self.stimilus = stimulus
        self.created = created
        self.updated = updated
        self.answer_order_matters = answer_order_matters
        self.sort_position = sort_position
        self.answers = answers if answers is not None else list()

    def question_type(self):
        if len(self.answers) >= 2:
            return MULTIPLE_CHOICE


class Answer:
    def __init__(self, id, content, created, updated, sort_position) -> None:
        self.id = id
        self.content = content
        self.created = created
        self.updated = updated
        self.sort_position = sort_position


class Stem(Question):
    def __init__(self, config: any, id, content, stimulus, created, updated, answer_order_matters, sort_position, answers) -> None:
        Question.__init__(self, config, id, stimulus, created,
                          updated, answer_order_matters, sort_position, answers)
        self.content = content

    def generate_question(self):
        return self.content

    def generate_answers(self):
        return [
            {"text": a.content,
                "correct": False if a.correctness == 0 else True,
             "tipsAndFeedback": {
                 "tip": "",
                 "chosenFeedback": a.feedback if a.feedback is not None else "",
                 "notChosenFeedback": ""
             }
             } for a in self.answers]


class StemAnswer(Answer):
    def __init__(self, id, content, created, updated, sort_position, correctness, feedback) -> None:
        Answer.__init__(self, id, content, created, updated, sort_position)
        self.correctness = correctness
        self.feedback = feedback
