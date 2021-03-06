from ._connection import EduCubeConnection
#from ._fake_connection import FakeEduCubeConnection 


def configure_connection(port, board, baud, fake=False, **kwargs):
    """
    Creates the appropriate EduCube connection object.

    """
#    logger.info("Creating educube connection")

    if fake:
        educube_connection = FakeEduCubeConnection(
            port, board, baud=baud
        )

    else:
        educube_connection = EduCubeConnection(
            port, board, baud=baud,
        )

    return educube_connection

