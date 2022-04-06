# Peac_LS
Language Server powers the editing experience for many programming languages. It allows implemntation of language features that many user expect, such as autocomplete, error-checking (diagnostics), jump-to-definition.

Peac_LS is a part of the *AI for Cloud Ops* initiative. It is a Language Server (a static code analysis tool) that can be reused in multiple editors by using the standardized the communication protocol between Language Server and a Language Client. Its language features will include AI-based analytics of systems data. 

### Architecture
![Architecture](https://user-images.githubusercontent.com/65934595/161632251-774f106a-1f0d-43f0-8eff-660484197c90.png)

## Foundational Work
One of the project that form the foundation of the *AI for Cloud Ops* initiative is Praxi. Please refer to the project README for more information. For this specific method of implementation, we are using the Language Server Protocol (LSP).

### Language Server Protocol (LSP)
The Language Server Protocol (LSP) defines the protocol used between an editor or IDE and a language server. Please refer to [Official LSP Website](https://microsoft.github.io/language-server-protocol/) for more information.

## Current Work
Peac_LS is being worked on in parallel to *iPython magic implementation* method of implementation. Currently, an example of a working plugin is made by using PyLS and cookiecutter. Ideally, we would like to create our very own working Language Server.

### pylsImports
Using cookiecutter and an existing Python Language Server (PyLS), this plugin highlights any part of the code that calls for an import of a module. Next steps include doing analysis in the backend and adding analytic messages toshow instead when users hover over the highlight.