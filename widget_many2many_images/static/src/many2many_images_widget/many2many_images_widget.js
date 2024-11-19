/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { FileInput } from "@web/core/file_input/file_input";
import { useX2ManyCrud } from "@web/views/fields/relational_utils";
import { Component, useState } from "@odoo/owl";

export class Many2manyImagesField extends Component {
	setup() {
		this.currentFile = {};
        this.files = useState(this.props.value.records.map((record) => record.data));
		this.orm = useService("orm");
		this.notification = useService("notification");
		this.operations = useX2ManyCrud(() => this.props.value, true);
        this.openRenameModal = this.openRenameModal.bind(this);
        this.saveRename = this.saveRename.bind(this);
		this.className = this.props.className ? `${this.props.className} w-100` : 'w-100';
	}

	getUrl(id) {
		return "/web/content/" + id;
	}

	getExtension(file) {
		return file.name.replace(/^.*\./, "");
	}

	async onFileUploaded(files) {
		for (const file of files) {
			if (file.error) {
				return this.notification.add(file.error, {
					title: this.env._t("Uploading error"),
					type: "danger",
				});
			}
			await this.operations.saveRecord([file.id]);
		}
	}

	async onFileRemove(deleteId) {
		const record = this.files.find(
			(record) => record.data.id === deleteId
		);
		this.operations.removeRecord(record);
	}

	openImageModal(url, name) {
		const modalImage = document.getElementById("modalImage");
		modalImage.src = url;
		document.getElementById("imageModalLabel").innerHTML = name;
		$("#imageModal").modal("show");
	}

	closeImageModal() {
		const modalImage = document.getElementById("modalImage");
		modalImage.src = "";
		document.getElementById("imageModalLabel").innerHTML = "";
		$("#imageModal").modal("hide");
	}

	// Open the rename modal
	openRenameModal(file) {
		this.currentFile = file;
		document.getElementById("newFileName").value = file.name; // Pre-fill the current name
		$("#renameModal").modal("show");
	}

	// Close the rename modal
	closeRenameModal() {
		$("#renameModal").modal("hide");
	}

	async saveRename() {
        const newName = document.getElementById("newFileName").value;
    
        if (newName && this.currentFile) {
            const updatedFile = { ...this.currentFile, name: newName };
            try {
                await this.orm.write("ir.attachment", [updatedFile.id], {
                    name: newName,
                });
                const index = this.files.findIndex(
                    (record) => {
                        return record.id === updatedFile.id
                    }
                );
                if (index !== -1) {
                    this.files[index].name = newName;
                }
                this.closeRenameModal();
                this.notification.add("File renamed successfully.", {
                    title: this.env._t("Success"),
                    type: "success",
                });
            } catch (error) {
                this.notification.add(error.message || "Failed to rename file.", {
                    title: this.env._t("Error"),
                    type: "danger",
                });
            }
        } else {
            this.notification.add("Please enter a valid name.", {
                title: this.env._t("Error"),
                type: "danger",
            });
        }
    }
}

Many2manyImagesField.template = "web.Many2manyImagesField";
Many2manyImagesField.components = {
	FileInput,
};
Many2manyImagesField.props = {
	...standardFieldProps,
	acceptedFileExtensions: { type: String, optional: true },
	className: { type: String, optional: true },
	uploadText: { type: String, optional: true },
};
Many2manyImagesField.supportedTypes = ["many2many"];
Many2manyImagesField.fieldsToFetch = {
	name: { type: "char" },
	mimetype: { type: "char" },
};

Many2manyImagesField.isEmpty = () => false;
Many2manyImagesField.extractProps = ({ attrs, field }) => {
	return {
		acceptedFileExtensions: attrs.options.accepted_file_extensions,
		className: attrs.class ? `${attrs.class} w-100` : 'w-100',
		uploadText: field.string,
	};
};

registry.category("fields").add("many2many_images", Many2manyImagesField);
