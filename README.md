# Run EC2 commands log output

Run commands on EC2 instances and log output using AWS Lambda. 

The commands are run on instances specified by specific tag. The lambda function does SSH connection into the EC2 servers. The PEM key is stored in AWS System's Manager's Parameter Store and can be encrypted to make sure its never exposed as plain text. This can help you to satisfy the securoty and compliance needs.

When command is run, the stdout output is collected together and logged into the prespecified s3 bucket. This is to make sure, if any error occures you should see it in the s3 logs.

## How it works : 

Step 1 : Lambda function gets environment variables from Lambda environment key value pairs
Step 2 : Get the key from AWS System Manager's Parameter Store and pass decryption parameter as true. The key should be encrypted when stored in the parameter store service. This will help to make sure it is never exposed plain text.
Step 3 : Get all instances in specified region based on specified EC2 tag key-value pair.
Step 4 : Login into the instances one by one and run commands
Step 5 : Log the command stdout output to s3 specified bucket


## Setup : 

    1. Go to AWS Systems Manager > Parameter Store and click on `Create Parameter`
    2. Add `name` as `MyEc2Pem`, Type as `SecureString`
    3. Paste the contents of ec2 pem file into `Value` section
    4. Select `KMS Key ID` to encrypt the pem key plain text string
    5. Go to AWS S3 and create a bucket called `lambda-logs`
    6. Go to all EC2 servers you want to run commands on and check if they have a common EC2 tag. If not please add one. If your EC2 servers are under a launch configurations then make sure that has a EC2 tag which will be added to all auto-scaling instances
    7. Go to AWS Lambda and click on `Create Function`
    8. Select `Author From Scratch`
    9. Add a function name as you want
    10 Select Runtime as `python 3.7`
    11. In `Function Code` upload the `function_package.zip` file
    12. Make sure the `Handler` is `lambda_function.lambda_handler`
    13. In `Environment variables` section add key value pairs for :
        command, ec2Region, ec2TagName, ec2TagValue, pemParameterName, s3Bucket, username
    14. In `Execution role` section click on the role `View The role..` url
    15. Add permissions to ReadSSMParameterStore, Store object in s3 and describe ec2 instances
    16. Save the function


## Customization and re-packaging : 

As you might be aware, the packages like paramiko are not present by default in the amazon instances where lambda function is run. We need to add the python executables in the lambda function itself in a zip file with the actual lambda function. 

~~~bash
cd ~
mkdir lambda
cd lambda
wget https://github.com/techsemicolon/ec2-run-commands-log-output/raw/master/function_package.zip
mkdir executables
mv function_package.zip executables/
cd executables/
unzip function_package.zip
~~~

Now edit the lambda file inside `lambda/executables/lambda_function.py` if you want ans save it

- Re-packaging : 

~~~bash
cd ~/lambda/executables
zip -r9 "../function_package_v2.zip" .
cd ../
~~~

Now you will have updated and repackaged `function_package_v2.zip` which you can upload into lambda function

## Note : 

Please ask questions if you are not sure about anything in github issues and will be happy to help. You are solely responsible for the actions you take on your AWS servers. This package is just to help you save lot of setup and packaging time. 