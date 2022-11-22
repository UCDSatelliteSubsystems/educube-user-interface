from ._connection import EduCubeConnection
#from ._fake_connection import FakeEduCubeConnection 


def configure_connection(port, board, baudrate, fake=False, **kwargs):
    """
    Creates the appropriate EduCube connection object.

    """
#    logger.info("Creating educube connection")

    if fake:
        educube_connection = FakeEduCubeConnection(
            port, board, baudrate=baudrate, **kwargs
        )

    else:
        educube_connection = EduCubeConnection(
            port, board, baudrate=baudrate, **kwargs
        )

    return educube_connection

