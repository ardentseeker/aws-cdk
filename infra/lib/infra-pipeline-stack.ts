import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as pipelines from "aws-cdk-lib/pipelines";
import { InfraStack } from "./infra-stack";

export class InfraPipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    const source = pipelines.CodePipelineSource.connection(
      "ardentseeker/aws-cdk",
      "main",
      {
        connectionArn:
          "arn:aws:codeconnections:us-east-1:639493421189:connection/8cc9db2e-8d57-4dfb-b33d-32ec7137d645",
      },
    );
    const pipeline = new pipelines.CodePipeline(this, "Pipeline", {
      pipelineName: "InfraPipeline",
      synth: new pipelines.ShellStep("Synth", {
        input: source,
        commands: ["cd infra", "npm ci", "cdk synth"],
      }),
    });
    pipeline.addStage(new DeployInfraStackStage(this, "DeployInfraStack"));
  }
}

export class DeployInfraStackStage extends cdk.Stage {
  constructor(scope: Construct, id: string, props?: cdk.StageProps) {
    super(scope, id, props);
    new InfraStack(this, "InfraStack");
  }
}
