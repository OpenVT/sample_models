
from cc3d import CompuCellSetup
        

from SimpleChemotaxisSteppable import SimpleChemotaxisSteppable

CompuCellSetup.register_steppable(steppable=SimpleChemotaxisSteppable(frequency=1))


CompuCellSetup.run()
