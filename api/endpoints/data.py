from fastapi import APIRouter

router = APIRouter()



@router.get('/')
def starter():
    print ("Halo")
    return 'Helo'