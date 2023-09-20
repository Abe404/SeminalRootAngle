bash lint.sh
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "Not running as lint problems found"
else
    echo "No lint problems"
fi

