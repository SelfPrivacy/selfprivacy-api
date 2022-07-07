import strawberry


@strawberry.interface
class MutationReturnInterface:
    success: bool
    message: str
    code: int


@strawberry.type
class GenericMutationReturn(MutationReturnInterface):
    pass
