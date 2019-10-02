# -*- python -*-
# ex: set filetype=python:

from buildbot.plugins import steps, util


def shellCommand(command, name, workdir="build", env={}, haltOnFailure=True, flunkOnFailure=True, warnOnFailure=True, alwaysRun=False, doStepIf=True, hideStepIf=False):
    return steps.ShellCommand(
        command=command,
        name=name,
        workdir=workdir,
        env=env,
        flunkOnFailure=flunkOnFailure,
        haltOnFailure=haltOnFailure,
        warnOnFailure=warnOnFailure,
        alwaysRun=alwaysRun,
        doStepIf=doStepIf,
        hideStepIf=hideStepIf)


def shellArg(command, logfile, haltOnFailure=True, flunkOnFailure=True, warnOnFailure=True):
    return util.ShellArg(
        command=command,
        logfile=logfile,
        flunkOnFailure=flunkOnFailure,
        haltOnFailure=haltOnFailure,
        warnOnFailure=warnOnFailure)


def shellSequence(commands, name, workdir="build", env={}, haltOnFailure=True, flunkOnFailure=True, warnOnFailure=True, alwaysRun=False, doStepIf=True, hideStepIf=False):
    return steps.ShellSequence(
        commands=commands,
        name=name,
        workdir=workdir,
        env=env,
        flunkOnFailure=flunkOnFailure,
        haltOnFailure=haltOnFailure,
        warnOnFailure=warnOnFailure,
        alwaysRun=alwaysRun,
        doStepIf=doStepIf,
        hideStepIf=hideStepIf)


def getMavenBase():
{% if skip_tests %}
    return ['mvn', '-B', '-V', '-Dmaven.repo.local=/builder/m2', '-DskipTests']
{% else %}
    return ['mvn', '-B', '-V', '-Dmaven.repo.local=/builder/m2']
{% endif %}


def getPreflightChecks():
    return shellSequence(
        commands=[
            shellArg(
                command="df /builds -m | tail -n 1 | awk '$4 <= {{ minimum_build_diskspace }} { exit 1 }'",
                logfile='freespace')
        ],
        name="Pre-flight checks")


def getClone():
    return steps.GitHub(
        repourl="{{ source_repo_url }}",
        mode='full',
        method='fresh',
        haltOnFailure=True,
        flunkOnFailure=True,
        name="Clone/Checkout")


def getWorkerPrep(deploy=False):
    mvn = getMavenBase()
    mvn.extend(['dependency:go-offline', '-fn'])
    commandsAry=[
        shellArg(
            command=['git', 'clean', '-fdx'],
            logfile='clean'),
        shellArg(
            command=mvn,
            logfile='deps')
    ]
    if deploy:
        commandsAry.append(shellArg(
            command="scp {{ buildbot_scp_settings }} settings.xml",
            logfile="settings"))
    return shellSequence(
        commands=commandsAry,
        name="Build Prep")


def getBuild(deploy=False):
    command = getMavenBase()
    if not deploy:
      command.extend(['clean', 'install'])
    else:
      command.extend(['clean', 'deploy', '-P', 'none', '-s', 'settings.xml'])
    return shellSequence(
        commands=[
            shellArg(
                command=['sed', '-i', 's/WARN/DEBUG/',
                         'docs/log4j/log4j.properties'],
                logfile='sed'),
            shellArg(
                command=command,
                logfile='build')
        ],
        name="Build")


def loadSigningKey():
    return shellCommand(
        command="scp {{ buildbot_scp_signing_key }} /dev/stdout | gpg --import",
        name="Load signing key")


def unloadSigningKey():
    return shellCommand(
        command=['rm', '-rf', '/builder/.gnupg'],
        alwaysRun=True,
        name="Key cleanup")


def getClean():
    return shellSequence(
        commands=[
            shellArg(
                command=['git', 'clean', '-fdx'],
                logfile='git')
        ],
        alwaysRun=True,
        name="Cleanup")
