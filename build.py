import argparse
import os
import sys

disabled_modules = [
    "arkit",
    "bmp",
    "bullet",
    "camera",
    "camera_iphone",
    "enet",
    "gdnative",
    "hdr",
    "icloud",
    "inappstore",
    "jsonrpc",
    "minimp3",
    "mobile_vr",
    "tinyexr",
    "upnp",
    "webxr"
]

enabled_modules = []

paired_options = {
    "deprecated": False,
    "no_editor_splash": True,
    "vulkan": False,

    "optimize": "speed",
    "arch": "x64",
    "platform": "windows",
    "target_win_version": "0x0A00"
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices={"editor", "game", "mono_gen"}, help="which application to build")
    parser.add_argument("-c", "--configuration", choices={"debug", "release"}, default="release", help="which build configuration to use")
    parser.add_argument("--mono", action="store_true", help="build with mono support enabled")
    parser.add_argument("--clean", action="store_true", help="clean the build system for the specified configuration")
    parser.add_argument("--no-cache", action="store_true", help="force scons to discard its build cache")

    args, pass_thru_args = parser.parse_known_args()

    if args.target == "editor" or args.target == "mono_gen":
        paired_options["tools"] = True
    else:
        paired_options["tools"] = False
        paired_options["disable_3d"] = True

    # check the tools option here rather than rerunning the same check
    if args.configuration == "release" and paired_options["tools"] == True:
        paired_options["target"] = "release_debug"
    else:
        paired_options["target"] = args.configuration
    
    if args.configuration == "debug" or args.target == "mono_gen":
        paired_options["use_lto"] = False
    else:
        paired_options["use_lto"] = True

    if args.configuration == "debug":
        paired_options["debug_symbols"] = True
    else:
        paired_options["debug_symbols"] = False

    if args.mono or args.target == "mono_gen":
        enabled_modules.append("mono")
        # for now use either mono or gdscript
        # except the editor requires gdscript to be enabled
        if paired_options["tools"] != True:
            disabled_modules.append("gdscript")
    
    if args.mono and args.target != "mono_gen":
        paired_options["mono_glue"] = True
        if args.configuration == "editor":
            # seems to be required, though docs claim otherwise
            paired_options["copy_mono_root"] = True
    elif args.target == "mono_gen":
        paired_options["mono_glue"] = False

    # sort this for ease of checking the command line
    # other params are left as-is since they are more logically-grouped
    disabled_modules.sort()
    enabled_modules.sort()

    cmdLine = build_command_line(args.clean, args.no_cache, pass_thru_args)
    print(cmdLine)
    os.system(cmdLine)


def build_command_line(doClean, doNoCache, additional_args):
    # scons multicore compile; leave 2 cores free for now
    additional_args.append("-j22")

    command_line = "scons "
    if doClean:
        command_line += "-c "
    if doNoCache:
        command_line += "--config=force "
    
    command_line += ''.join(map(lambda x: f"module_{x}_enabled=no ", disabled_modules))
    command_line += ''.join(map(lambda x: f"module_{x}_enabled=yes ", enabled_modules))

    # this probably shouldn't be a lambda
    # and there are probably a dozen better ways to do this
    # turn True/False into "yes"/"no", leave other values untouched
    test = dict(map(lambda x: (x[0], "yes" if (type(x[1]) == type(True) and x[1] == True) else "no" if (type(x[1]) == type(True) and x[1] == False) else x[1]), paired_options.items()))
    command_line += ''.join([f"{key}={value} " for key, value in test.items()])

    command_line += ' '.join(additional_args)

    return command_line


if __name__ == "__main__":
    main()
