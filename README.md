# AI for cloud ops

BU faculty members Ayse Coskun, Alan Liu, and Gianluca Stringhini, along with Red Hat researcher Marcel Hild will pursue work at the intersection of artificial intelligence (AI) and cloud systems through this joint project, ai-for-cloud-ops. 

The researchers intend to create new methods for fusing and representing systems data to enable AI-based analytics and will build, apply, and scale AI frameworks to improve performance, management, security, compliance, and resilience problems in the cloud. 


>"We aim to help deliver easily-accessible and open source AI technologies that will cater to both developers and administrators solving real-world performance, resilience, and security challenges” 


## Foundational Work
The following projects form the foundation of the *AI for Cloud Ops* initiative. We plan to incorporate these into our unified framework; in the meantime, we encourage you to try each one out and open issues (in each project's respective repository) with any ideas for potential improvements!

### ACE
Approximate Concrete Execution (ACE) is a just-in-time binary analysis technique that enables automatic detection of undesirable components in executable binaries found in serverless and other cloud applications without requiring a trusted build system. With ACE, we contribute a novel method of creating function fingerprints just before serverless software is first-executed, in which we execute an intermediate representation of the code in an approximate virtual machine and use the resulting context as the fingerprint. ACE fingerprints can then be compared to a function blocklist using simple vector distance metrics or searched for in a k-nearest-neighbor fashion. In our evaluation, we find that ACE performs these tasks with comparable accuracy 5.2x faster than a state-of-the-art method. More details are available in our [WoSC 2020 paper](https://www.bu.edu/peaclab/files/2020/12/ACE-WoSC2020.pdf) and in our [GitHub repo](https://github.com/peaclab/ace).

### Iter8
Iter8, an open-source system that enables practitioners to deliver code changes to cloud applications in an agile manner while minimizing risk. Iter8 embodies our novel mathematical formulation built on online Bayesian learning and multi-armed bandit algorithms to enable online experimentation tailored for the cloud, considering both SLOs and business concerns, unlike existing solutions. Using Iter8, practitioners can safely and rapidly orchestrate various types of online experiments, gain key insights into the behavior of cloud applications, and roll out the optimal versions in an automated and statistically rigorous manner. More details available in our [SOCC 2021 paper](https://www.bu.edu/peaclab/files/2022/01/Iter8-socc21.pdf) and on the [project website](https://iter8.tools/). 

### Praxi
Praxi is a tool for discovering software running in the cloud using machine learning. Users can create a corpus of “changesets” representing the software they’d like to discover on their cloud systems (e.g., insecure server applications like Telnet or resource-stealing applications like crypto-currency miners) using Praxi’s filesystem fingerprint recording tool, which can then be used to train a machine learning model. Users can then run Praxi as a daemon, using the trained model to predict whether current filesystem activity matches that of an application in the corpus. Thanks to Praxi’s low overhead and incremental training ability, it’s well-suited to long-term deployments on cloud systems of all sizes. More details available in our [TCC 2019 paper](http://www.bu.edu/peaclab/files/2020/03/PraxiJournal.pdf) and in our [GitHub repo](https://github.com/peaclab/ace).

## Join the Project!

If you want to learn more about this project and get involved, come say 'Hi!'and ask questions in the #ai4cloudops channel on the [Operate First Slack](https://join.slack.com/t/operatefirst/shared_invite/zt-o2gn4wn8-O39g7sthTAuPCvaCNRnLww).
We also invite you to join our [monthly community Zoom meetings](https://bostonu.zoom.us/j/98113583702?pwd=akQ3c3lKOG1NZ2tNRFFUSlNGRXhCQT09) on the first Wednesday of every month at 10am U.S. Eastern.

Or, go ahead an open an issue in this repo. 
