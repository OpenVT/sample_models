
from cc3d.core.PySteppables import *

class SimpleChemotaxisSteppable(SteppableBasePy):

    def __init__(self,frequency=1):

        SteppableBasePy.__init__(self,frequency)

    def start(self):
        #define space and timescales
        self.MCS_TIME=1 #ms
        self.VOX_SPACE=1 #um2/um2
        self.lambda_chemo=5000.0 #value of Lambda Chemotaxis
        half_gaussian=0.0
        exp_decay=0.0
        # any code in the start function runs before MCS=0
        #define the type and shape of the static field
        field = self.field.Attr
        # field = self.getConcentrationField("Attr") THIS DOES NOT EXIST ANYMORE; FIX ON READ THE DOCS
        if half_gaussian == 1.0:
            sig=100
            maxValue = np.sqrt(2/np.pi)/sig*np.exp(-0.5*(0)**2)
            for a in range(500):
                #half gaussian 0 to 1
                val = np.sqrt(2/np.pi)/sig*np.exp(-0.5*(a/sig)**2)/maxValue #find value of half gaussian 0 to 1
                field[499-a, 0:64:1 ,0]=val #flip to allow max value at RHS
        elif exp_decay == 1.0:
            for a in range(500):
                #linear 0 to 1
                lam=0.005
                field[499-a, 0:64:1 ,0] = np.exp(-lam*a)
        else:
            for a in range(500):
                #linear 0 to 1
                field[a, 0:64:1 ,0] = a/499

        #decaying exponential 0 to 1 (To ADD)
        
        #e^(-lam*x)
        
        #define formula used for chemotatic sensing
        for cell in self.cellList:
            if cell.type == self.cell_type.cell:
                cell.lambdaVolume=2 
                cell.targetVolume=100
                cd = self.chemotaxisPlugin.addChemotaxisData(cell, "Attr")
                #define what type of sensing you want allowed ; see https://pythonscriptingmanual.readthedocs.io/en/latest/chemotaxis_plugin.html
                #for the forms of equations
                cd.setLambda(self.lambda_chemo)
                #cd.setSaturationCoef(0.02) #saturation (what level is needed to sense [x/(x+sat), smaller values make it more sensitive])
                #cd.setLogScaledCoef(0.002) #log scaled (differs by seting a scalar value to be added to lambda normalization[lam/(coef+concentration)])
        
        # Set Parameter values here and create persistent variables
        self.nflips=100 # number of times to average velocity for each parameter set across mcs
                 
        
        # for cell in self.cellList:
            # if cell:
                # cell.lambdaVolume=2 # In this simulation I am scanning lambda volume between min_value and max_value
                # cell.targetVolume=100
                # # we will give the cell a way to keep track of its velocity by tracking the last time and x position we changed direction
                # cell.dict['lastDirectionChangeTime'] = 100
                # cell.dict['lastDirectionChangePosition'] = 0
                # cd = self.chemotaxisPlugin.addChemotaxisData(cell, "Attr")
                # #print(dir(cd))
                # cd.setLambda(self.lambda_chemo)
                # #set initial value of lambda chemo
                   
        self.pW = self.addNewPlotWindow(_title='Center of Mass', _xAxisTitle='MonteCarlo Step (MCS)',
                                        _yAxisTitle='Variables', _xScaleType='linear', _yScaleType='linear')
        self.pW.addPlot('XPosition', _style='Dots', _color='red', _size=5)
        self.pW.addPlot('YPosition', _style='Dots',_color='blue', _size=5)
        self.pW2 = self.addNewPlotWindow(_title='Velocity', _xAxisTitle='MonteCarlo Step (MCS)',
                                        _yAxisTitle='Variables', _xScaleType='linear', _yScaleType='linear')
        self.pW2.addPlot('XVelocity', _style='Dots', _color='red', _size=5)
        self.pW2.addPlot('YVelocity', _style='Dots',_color='blue', _size=5)
        self.pW3 = self.addNewPlotWindow(_title='Velocity vs parameter', _xAxisTitle='Lambda Chemo',
                                        _yAxisTitle='Mean Velocity', _xScaleType='linear', _yScaleType='linear')
        self.pW3.addPlot('XVelocity', _style='Dots', _color='red', _size=5)
        self.xPos=[]
        self.yPos=[]
        self.velocity_list=[]
        

    def step(self,mcs):
        #We want to calculate the velocity of the cell as a function of time. 
        #We will end when the cell when it gets within 5% of the x max positions or hits max time.
        
        for cell in self.cellList: 
            self.pW.addDataPoint("XPosition", mcs, cell.xCOM)  
            self.pW.addDataPoint("YPosition", mcs, cell.yCOM)
            self.xPos.append(cell.xCOM)
            self.yPos.append(cell.yCOM)
            if mcs==0:
                cell.dict['lastPosition'] = cell.xCOM
            if mcs%self.nflips==0 and mcs>0: #Set initial x position after stabilization
                mean_x_velocity=abs(cell.xCOM-cell.dict['lastPosition'])/self.nflips
                self.velocity_list.append(mean_x_velocity)# add velocity measurement to the stack
                #vy=(cell.yCOM-self.yPos[-100])/100.0
                self.pW2.addDataPoint("XVelocity", mcs, mean_x_velocity)  
                #self.pW2.addDataPoint("YVelocity", mcs, vy)
                cell.dict['lastPosition'] = cell.xCOM
                
            if (cell.xCOM > self.dim.x*0.95):
                self.stop_simulation()            

    def finish(self):
        """
        Finish Function is called after the last MCS
        """

    def on_stop(self):
        # this gets called each time user stops simulation
        return


        