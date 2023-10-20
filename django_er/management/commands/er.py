import os
import platform
import sys
import uuid
from typing import Optional

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import models


class Mermaid:
    def __init__(self, diagram: str):
        self._diagram = self._process_diagram(diagram)
        self._uid = uuid.uuid4()

    @staticmethod
    def _process_diagram(diagram: str) -> str:
        _diagram = diagram.replace("\n", "\\n")
        _diagram = _diagram.lstrip("\\n")
        return _diagram

    def html(self) -> str:
        ret = f"""
<!DOCTYPE html>
<head>
    <title>ER图</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
</head>
<body>
    <pre class="mermaid">
      {self._diagram}
    </pre>
    <script type="module">
        mermaid.initialize( {{ theme: 'default', er: {{useMaxWidth: false, layoutDirection: "LR"}} }} );
    </script>
</body>
</html>
"""
        return ret


class Command(BaseCommand):
    help = "Creates er for apps."

    def add_arguments(self, parser):
        parser.add_argument("args", metavar="app_label", nargs="*", help="Specify the app label(s) to create er for.")
        parser.add_argument("-o", "--output", help="Specifies file to which the output is written.")

    def handle(self, *app_labels, **options):
        # Make sure the app they asked for exists
        app_labels = set(app_labels)
        has_bad_labels = False
        check_labels = set()
        for app_label in app_labels:
            try:
                check_labels.add(apps.get_app_config(app_label).label)
            except LookupError as err:
                self.stderr.write(str(err))
                has_bad_labels = True
        if has_bad_labels:
            sys.exit(2)
        if not check_labels:
            check_labels = {config.label for config in apps.get_app_configs()}
        html = self._generate_er(check_labels)
        self._out(options["output"], html)

    def _generate_er(self, check_labels: list[str]) -> str:
        # https://mermaid.js.org/syntax/entityRelationshipDiagram.html
        er = "erDiagram"
        relation_er = ""
        for app_label in check_labels:
            for model in apps.get_app_config(app_label).get_models():
                # 表信息生成
                table_name = model._meta.db_table
                table_comment = model._meta.verbose_name
                er += f' {table_name}["{table_name}({table_comment})"] {{'
                fields: list[models.Field] = model._meta.fields

                for f in fields:
                    # 字段描述生成
                    choices = ",".join((f"{k}:{v}" for k, v in f.choices or []))
                    type_ = f.get_internal_type()
                    if f.max_length:
                        type_ += f"({f.max_length})"
                    comment = f"{f.verbose_name} {f.help_text} {choices}".strip().replace('"', r"\'")
                    field_item = f'{type_} {f.column} "{comment}"'
                    item_length = 120
                    if len(field_item) > item_length:
                        field_item = field_item[: item_length - 4] + '.."'
                    er += " " + field_item
                    # 关系生成
                    if isinstance(f, (models.ForeignKey, models.OneToOneField, models.ManyToManyField)):
                        rhs_field: models.Field = f.foreign_related_fields[0]
                        rhs_table_name = rhs_field.model._meta.db_table
                        if f.many_to_one:
                            relation = " }o--|| "
                        elif f.one_to_one:
                            relation = " ||--|| "
                        elif f.many_to_many:
                            relation = " }o--o{ "
                        elif f.one_to_many:
                            relation = " ||--o{ "
                        relation_er += " " + table_name + relation + rhs_table_name + f":{f.column}"
                er += "}"
        er += relation_er
        if len(er) > 50000:
            self.stderr.write("ER is to large, plseae select apps to generate")
            sys.exit(2)
        if er == "erDiagram":
            self.stdout.write("There are no modules, please create module first.")
            sys.exit(0)
        html = Mermaid(er).html()
        return html

    def _out(self, output: Optional[str], string: str):
        if output:
            with open(output, "wt") as f:
                f.write(string)
            self.open_with_browser(output)
        else:
            self.stdout.write(string)

    @staticmethod
    def open_with_browser(filepath: str):
        os_name = platform.system()
        if os_name == "Linux":
            os.system(f"xdg-open {filepath}")
        elif os_name == "Windows":
            os.system(f"start {filepath}")
        elif os_name == "Darwin":
            os.system(f"open {filepath}")