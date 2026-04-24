from inginious_container_api import feedback
import subprocess
import os


##EXECUTION##


#java_jar = f"/opt/jplag/jplag-{os.environ["JPLAG_VERSION"]}jar-with-dependencies.jar"
java_jar = os.environ["JPLAG_JAR"]
extractfolder = "test"

try:
    subprocess.call(['java', '-jar', java_jar, extractfolder])
except Exception as e:
    print("Error while running jplag: {}".format(e))


# set the global result
feedback.set_global_result("success")  # Set global result to success