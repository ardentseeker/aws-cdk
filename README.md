##Important Command of CDK
1. cdk init - Initializes a cdk project and creates the basic skeleton.
2. cdk bootstrap - Prepres the env for the cdk to perform the deploy operaion
eg: preparing the require role, s3 creation for keeping the asset 
3. cdk synth - Synthesizes the code into cloudformation templates
4. cdk deploy - Synthesizes and deploys the code to the env
eg: synth -> cfn template -> deploy


##Flow of the project
Application stack -> pipeline stack -> bin/app.ts(entrypoint)

##Git commands for work
git remote set-url origin <value>
