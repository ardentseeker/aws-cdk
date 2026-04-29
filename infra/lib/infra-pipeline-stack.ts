import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as pipelines from "aws-cdk-lib/pipelines";
import { InfraStack } from "./infra-stack";
import * as codecommit from "aws-cdk-lib/aws-codecommit";

export class InfraPipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const repo = codecommit.Repository.fromRepositoryName(
      this,
      "CodeRepo",
      "aws-cdk",
    );
    const source = pipelines.CodePipelineSource.codeCommit(repo, "main");
    const pipeline = new pipelines.CodePipeline(this, "Pipeline", {
      pipelineName: "InfraPipeline",
      selfMutation: true,
      synth: new pipelines.ShellStep("Synth", {
        input: source,
        commands: [
          "cd infra",
          "npm ci",
          "npx cdk synth --context skipAssetBuild=true"
        ],
        primaryOutputDirectory: "infra/cdk.out",
      }),
    });

    pipeline.addStage(new DeployInfraStackStage(this, "DeployInfraStack"));
  }
}

export class DeployInfraStackStage extends cdk.Stage {
  constructor(scope: Construct, id: string, props?: cdk.StageProps) {
    super(scope, id, props);
    // Pipeline builds the actual Docker image - no skip flag here
    new InfraStack(this, "InfraStack");
  }
}
