import subprocess
import smtplib
import re
import os

object_types = {"pod", "service", "pvc"}

def remove_cluster_objects(whitelist):
    removed = []
    remove = False
    for object in object_types:
        result = subprocess.Popen("kubectl get %s -n keos-ci -o json | jq -r '.items[] | select((now - (.metadata.creationTimestamp | fromdateiso8601)) > 259200) | .metadata.name'" % (object), shell=True, stdout=subprocess.PIPE)
        for line in result.stdout.readlines():
            formated_line = line.strip().decode("utf-8")
            print("Object: " + formated_line)
            for item in whitelist:
                if not re.match(item.strip(), formated_line):
                    remove = True
                else:
                    remove = False
                    break
            if remove:
                removed.append({"object": object, "name": formated_line})
                remove_result = subprocess.Popen("kubectl delete %s %s --force -n keos-ci" % (object, formated_line), shell=True, stdout=subprocess.PIPE)
                print("Removed object: %s" % (str(remove_result.stdout.readlines())))
    return removed


def send_mail(data):
    email_from = "jenkins@stratio.com"
    email_to = "cd@stratio.com"
    email_username = "jenkins@stratio.com"
    email_password = os.getenv('MAILPASS')

    #Generate headers
    mail_subject = "[k8s Cronjobs] keoscicd-cleaner cronjob results"
    mail_body = "Cleaner job has removed %i objects from de keos-ci namespace.\nList of objects removed:\n\n" % (len(data))
    for item in data:
        mail_body += "%s %s\n" % (item["object"].upper(), item["name"])

    #Send mail
    message = 'Subject: {}\n\n{}'.format(mail_subject, mail_body)
    server = smtplib.SMTP_SSL("smtp.gmail.com")
    server.login(email_username, email_password)
    server.sendmail(email_from, email_to, message)
    server.quit()


def main ():
    with open("/keoscicd-cleaner-whitelist/keoscicd-cleaner-whitelist") as f:
        whitelist = f.readlines()
    removed = remove_cluster_objects(whitelist)
    send_mail(removed)


if __name__ == '__main__':
    main()
