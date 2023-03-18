import os


def open_pipe(clear=False):
    if os.path.exists("/home/pi/scrimblopipe"):
        pipe = open("/home/pi/scrimblopipe", "w")
        if clear:
            pipe.write("CLEAR")
            pipe.flush()

        return pipe


def send_pipe(pipe, messages):
    if pipe:
        for st in messages:
            pipe.write(st)
            pipe.flush()


def send_prot_msg(pipe, st):
    sts = []

    if len(st) > 4096:
        buffer = ""
        for part in st.split("|"):
            if len(buffer + part + "|") > 4096:
                sts.append(buffer)
                buffer = part + "|"
            else:
                buffer += part + "|"

        sts.append(buffer)
    else:
        sts = [st]

    send_pipe(pipe, sts)
