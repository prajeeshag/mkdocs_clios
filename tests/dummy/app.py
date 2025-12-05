from clios import Clios, OperatorFns

operatorfns = OperatorFns()


@operatorfns.register()
def dummy_operator() -> str:
    return "DOC"


app = Clios(operatorfns)
