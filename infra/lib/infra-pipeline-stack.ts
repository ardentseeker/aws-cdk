import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as pipelines from 'aws-cdk-lib/pipelines';
import { InfraStack } from './infra-stack';

export class InfraPipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    const source = pipelines.CodePipelineSource.gitHub('roush/infra', 'main', {
      authentication: cdk.SecretValue.secretsManager('github-token'),
    });
    const pipeline = new pipelines.CodePipeline(this, 'Pipeline', {
      pipelineName: 'InfraPipeline',
      synth: new pipelines.ShellStep('Synth', { 
        input: source,
        commands: [
          'npm ci',
          'cdk synth'
        ]
      })
    });
    pipeline.addStage(new DeployInfraStackStage(this, 'DeployInfraStack'));}
}

export class DeployInfraStackStage extends cdk.Stage {
  constructor(scope: Construct, id: string, props?: cdk.StageProps) {
    super(scope, id, props);
    new InfraStack(this, 'InfraStack');
  }
}