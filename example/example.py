from inskrib.autograph import Autograph
from inskrib.documents import Document


autograph = Autograph(size=(380, 380))
document = Document()

document.get_authoraphs('./data', autograph)
