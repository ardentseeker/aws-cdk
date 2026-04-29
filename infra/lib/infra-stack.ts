import * as cdk from "aws-cdk-lib/core";
import { Construct } from "constructs";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as elbv2 from "aws-cdk-lib/aws-elasticloadbalancingv2";
// import * as sqs from 'aws-cdk-lib/aws-sqs';

export class InfraStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    const vpc = this.createVPC(this);
    const skipAssetBuild = this.node.tryGetContext("skipAssetBuild") === "true";
    const dockerImage = this.createAssets();
    this.createEcsWebService(this, vpc, dockerImage);
  }

  createAssets() {
    // Built in AWS CodeBuild when deployed via pipeline
    const dockerImage = ecs.ContainerImage.fromAsset("../", {
      exclude: ["infra", "node_modules", ".git"],
      file: "Dockerfile",
    });
    return dockerImage;
  }

  createVPC(scope: Construct): ec2.Vpc {
    // Create a VPC with public and private subnets
    const vpc = new ec2.Vpc(scope, "MyVPC", {
      vpcName: "MyVPC",
      maxAzs: 2,
      natGateways: 1,
      restrictDefaultSecurityGroup: false, // Avoids Lambda custom resource
    });
    return vpc;
  }

  createEcsWebService(
    scope: Construct,
    vpc: ec2.Vpc,
    dockerImage: ecs.ContainerImage,
  ) {
    // Create an ECS cluster
    const cluster = new ecs.Cluster(scope, "EcsCluster", {
      vpc: vpc,
      clusterName: "MyEcsCluster",
    });

    // Create a Fargate task definition
    const taskDefinition = new ecs.FargateTaskDefinition(scope, "TaskDef", {
      memoryLimitMiB: 512,
      cpu: 256,
    });

    // Add a container to the task definition
    const container = taskDefinition.addContainer("WebContainer", {
      image: dockerImage,
      logging: ecs.LogDrivers.awsLogs({ streamPrefix: "WebContainer" }),
      portMappings: [{ containerPort: 80 }],
    });

    // Create a Fargate service
    const service = new ecs.FargateService(scope, "FargateService", {
      cluster,
      taskDefinition,
      desiredCount: 2,
    });

    //Create an Application Load Balancer
    const loadBalancer = new elbv2.ApplicationLoadBalancer(scope, "ALB", {
      vpc,
      internetFacing: true,
    });

    // Add a listener to the load balancer
    const listener = loadBalancer.addListener("Listener", {
      port: 80,
    });

    // Add the ECS service as a target to the listener
    listener.addTargets("EcsTargets", {
      port: 80,
      targets: [service],
    });

    // Output the load balancer URL
    new cdk.CfnOutput(scope, "ServiceURL", {
      value: `http://${loadBalancer.loadBalancerDnsName}`,
    });

  }
}
