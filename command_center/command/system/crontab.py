from crontab import CronTab, CronItem
from termcolor import colored, cprint
from command_center.command import ValueInput, print_help_msg, ToolCommandMixin
from command_center.command.command import hostname


def show_crontab():
    crontab = CronTab(user=True)
    for cron_item in crontab.crons:
        cprint(cron_item, 'green')


class CronTabCommand(ToolCommandMixin):
    intro = colored('CronTab Command.\nType help or ? to list commands.\n', 'yellow')
    prompt = colored('%s (system - crontab)# ' % hostname, 'cyan')
   
    def help_show(self):
        print_help_msg("Show Current Crontab",
                       usage=["(system - crontab)# show"])

    def do_show(self, args):
        show_crontab()

    def help_add(self):
        print_help_msg("Add New Command To Crontab Line",
                       usage=["(system - crontab)# add",
                              "Run Cycle Setting > * * * * *",
                              "Run Command Setting > echo hello",
                              "Are you sure you want to add it? (* * * * * echo hello) [y/n] y"])

    def do_add(self, args):
        add_item = CronItem()
        cycle = ValueInput("Run Cycle Setting > ")
        try:
            add_item.setall(cycle)
        except Exception as e:
            cprint(str(e), 'red')
            return
        command = ValueInput("Run Command Setting > ")
        add_item.set_command(command)
        add_item.valid = True
        
        flag = ValueInput("Are you sure you want to add it? (" + cycle + " " + command + ") [y/n] > ")
        
        flag = flag.split('\n')[0].strip()
        if flag == "Y" or flag == "y":
            crontab = CronTab(user=True)
            crontab.append(add_item)
            crontab.write_to_user()

    def help_remove(self):
        print_help_msg("Remove Command From Crontab",
                       usage=["(system - crontab)# remove",
                              "0. * * * * * echo hello",
                              "1. 5 * * * * echo world",
                              "          ...          ",
                              "n. * * * * * do-something",
                              "Please select the item you want. [0-n] > 0",
                              "Are you sure you want to delete it? (* * * * * echo hello) [y/n] y"])

    def do_remove(self, args):
        crontab = CronTab(user=True)
        selected_idx = self.select_cron(crontab)
        if selected_idx == -1:
            return
        remove_item = crontab.crons[selected_idx]
        
        flag = ValueInput("Are you sure you want to delete it? (" + str(remove_item) + ") [y/n] > ")
        
        flag = flag.split('\n')[0].strip()
        if flag == "Y" or flag == "y":
            crontab.remove(remove_item)
            crontab.write_to_user()

    def help_edit(self):
        print_help_msg("Edit(Modify) Crontab",
                       usage=["(system - crontab)# edit",
                              "0. * * * * * echo hello",
                              "1. 5 * * * * echo world",
                              "          ...          ",
                              "n. * * * * * do-something",
                              "Please select the item you want. [0-n] > 0",
                              "Original Cron : * * * * * echo hello",
                              "Run Cycle Setting > * * * * 1",
                              "Run Command Setting > echo hello(mod)",
                              "Are you sure you want to edit it? (* * * * 1 echo hello(mod)) [y/n] > y"])

    def do_edit(self, args):
        crontab = CronTab(user=True)
        selected_idx = self.select_cron(crontab)
        if selected_idx == -1:
            return
        edit_item = crontab.crons[selected_idx]
        cprint("Original Cron : " + edit_item.render(), "yellow")
        cycle = ValueInput("Run Cycle Setting > ")
        try:
            edit_item.setall(cycle)
        except Exception as e:
            cprint(str(e), 'red')
            return
        command = ValueInput("Run Command Setting > ")
        edit_item.set_command(command)
        edit_item.valid = True
        
        flag = ValueInput("Are you sure you want to edit it? (" + str(edit_item) + ") [y/n] > ")
        
        flag = flag.split('\n')[0].strip()
        if flag == "Y" or flag == "y":
            crontab.crons[selected_idx] = edit_item
            crontab.write_to_user()
            
    def select_cron(self, crontab):
        # -1 error return
        selected_idx = -1
        cron_length = len(crontab.crons)
        if not cron_length > 0:
            cprint("No crontab settings have been added.", 'red')
            return selected_idx
            
        for idx, cron_item in enumerate(crontab.crons):
            print(colored(str(idx) + ". ", 'yellow') + colored(str(cron_item), 'green'))
        try:
            selected_idx = int(ValueInput("Please select the item you want. [0-"+str(cron_length-1)+"] > ", valuetype=int))
        except ValueError as e:
            cprint("Please enter a number. [0-"+str(cron_length-1)+"]", 'red')
            return selected_idx
        if selected_idx > cron_length and selected_idx < 0:
            cprint("Please enter a number. [0-"+str(cron_length-1)+"]", 'red')
            return selected_idx
        return selected_idx
