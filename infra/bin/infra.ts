#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib/core';
import { InfraPipelineStack } from '../lib/infra-pipeline-stack';

const app = new cdk.App();
new InfraPipelineStack(app, 'InfraPipelineStack', {
});
