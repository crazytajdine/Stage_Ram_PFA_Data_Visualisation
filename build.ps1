Write-Output "Starting to do job"


poetry run nuitka --standalone dashboard/test.py
