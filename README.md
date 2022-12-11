# Bootstrap Advantage Estimation (BAE)

Paper Title: Bootstrap Advantage Estimation for Policy Optimization in Reinforcement Learning. (ICMLA 2022).

## Installation
This codebase is based on the [CleanRL](https://github.com/vwxyzjn/cleanrl) library. Please follow the installation instructions on the official library site. The code should run on version [CleanRL v1.0.0b1](https://github.com/vwxyzjn/cleanrl/tree/v1.0.0b1). It might work on the latest version; however, some modifications might be needed.

The Procgen environments are based on image-based observation, and the policy and value networks use CNN-based models. Thus it is recommended to run those experiments on a GPU-enabled machine.

The experiments on DeepMind Control and PyBullet environments should run on the CPU.

For DeepMind Control environments, we use [dmc2gym](https://github.com/zuoxingdong/dm2gym) to convert the environments to OpenAI Gym format to be compatible with CleanRL. Please follow the instruction in the original repository for installation. A copy of the repository is provided here as well.


Please contact the author at rahman64@purdue.edu if you have any queries.
