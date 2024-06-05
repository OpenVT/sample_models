Local_Path=`pwd`
PhysiCell_path="../../../PhysiCell"
cp -r ../SimpleChemotaxis ${PhysiCell_path}/user_projects
ls ${PhysiCell_path}/user_projects
cd ${PhysiCell_path}
make PROJ=SimpleChemotaxis load
make