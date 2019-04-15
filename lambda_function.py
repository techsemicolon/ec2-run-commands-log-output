import boto3
import paramiko
import os
import datetime
from io import StringIO

# AWS Lambda :
# Runtime : Python 3.7 
# Handler : lambda_function.lambda_handler

def lambda_handler(event, context):

    # Get all variables specified in lambda function's environment
    # as key value pairs

    # Name of pem key stored in AWS Systems Manager's Parameter Store
    pemParameterName = os.environ['pemParameterName']
    # Tag name of EC2 servers e.g. ec2-identifier
    ec2tagName = os.environ['ec2TagName']
    # Tag value of EC2 servers e.g. production-instances
    ec2tagValue = os.environ['ec2TagValue']
    # Username of the server ssh e.g. ubuntu or ec2-user
    username = os.environ['username']
    # Shell command to run e.g. cd /var/www/scripts/deploy.sh
    command = os.environ['command']
    # Region of EC2 instances
    ec2Region = os.environ['ec2Region']
    # S3 Bucket Name
    s3Bucket = os.environ['s3Bucket']

    # Get pem key's actual decrepted value from 
    # AWS Systems Manager's Parameter Store
    pem = get_parameter_from_ssm(pemParameterName)
    
    # Invalid pem key
    if(pem is None):
        print('Invalid pem key')

    # Get all instances which have specified tag key value pair
    instances = get_instances_from_tag(ec2tagName, ec2tagValue, ec2Region)

    # No instances found
    if(len(instances) == 0):
        print('No instances found under provider tag')

    # Run command
    shellOutput = run_command(command, instances, pem, username)

    # Log the output to s3
    log_output_to_s3(shellOutput, s3Bucket)

    return { 
        'Done' : 1,
        'Output' : shellOutput
    }
    
def log_output_to_s3(shellOutput, s3Bucket):

    # Initialize s3 client
    s3 = boto3.resource('s3')

    # Make log file object name
    timestamp = datetime.datetime.now().strftime("%B %d, %Y %I:%M%p")
    objectName = timestamp + '-shelloutput.log'

    # Initialize new log file object
    logObject = s3.Object(s3Bucket, objectName)
    logObject.put(Body=shellOutput)

    return


def run_command(command, instances, pem, username):

    # Initialize command output string
    commandOutput = ''

    # Make key from pem string
    key = paramiko.RSAKey.from_private_key(StringIO(pem))

    # Initialize paramiko ssh client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    

    for instance in instances:

        # Print few details of the instance
        commandOutput += str("Running command on instance with ID : " + instance['InstanceId'] + "\n")
        
        try:
            # Connect/ssh to an instance
            # Here 'ubuntu' is user name and 'instance_ip' is public IP of EC2
            client.connect(hostname=instance['PublicIpAddress'], username=username, pkey=key)

            # Execute the command
            stdin, stdout, stderr = client.exec_command(command)

            # Add the stdout read to the command output
            commandOutput += str("\n Output : \n")
            commandOutput += str(stdout.read().decode('ascii'))

            # Close the ssh client
            client.close()

        except paramiko.ssh_exception.AuthenticationException:
            commandOutput += str("Error : Authentication Failed, please check if pem key is correct!\n")
        except paramiko.ssh_exception.SSHException:
            commandOutput += str("Error : Unable to SSH into the server!\n")

        commandOutput += str("\n---------------------------------------\n")


    return commandOutput

def get_parameter_from_ssm(parametername):

    # Initialize ssm client
    ssmclient = boto3.client('ssm')

    # Get paramater based on parameter name
    # Decrypt and get plain text value
    parameter =  ssmclient.get_parameter(
        Name=parametername,
        WithDecryption=True
    )

    return parameter['Parameter']['Value'] or None


def get_instances_from_tag(tagkey, tagvalue, ec2Region):

    # Initialize ec2 client
    ec2client = boto3.client('ec2', region_name=ec2Region)

    # Get all instances having specific tag and value
    response = ec2client.describe_instances(
        Filters=[
            {
                'Name': 'tag:' + tagkey,
                'Values': [tagvalue]
            }
        ]
    )

    instancesByTag = []

    for reservation in (response["Reservations"]):

        for instance in reservation["Instances"]:
            
            instancesByTag.append(instance)
    
    return instancesByTag