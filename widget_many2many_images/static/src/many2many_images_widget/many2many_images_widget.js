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

		this.openDeleteConfirmModal = this.openDeleteConfirmModal.bind(this);
        this.confirmDelete = this.confirmDelete.bind(this);
        this.closeDeleteConfirmModal = this.closeDeleteConfirmModal.bind(this);
	}

	getUrl(id) {
		return "/web/content/" + id;
	}

	getExtension(file) {
		if (file && file.name) {
			return file.name.replace(/^.*\./, "");
		} else {
			return "";
		}
	
	}

	async onFileUploaded(files) {
		for (const file of files) {
			if (file.error) {
				this.notification.add(file.error, {
					title: this.env._t("Tải file lên thất bại"),
					type: "danger",
				});
				return;
			}
			await this.operations.saveRecord([file.id]);
			const newFile = { id: file.id, name: file.name, data: file.data };
			this.files = [...this.files, newFile];
	
			this.notification.add("Tải file lên thành công.", {
				title: this.env._t("Success"),
				type: "success",
			});
		}
	}
	
	openDeleteConfirmModal(file) {
        this.currentFile = file;
        $('#deleteConfirmModal').modal('show'); 
    }

	closeDeleteConfirmModal() {
        $('#deleteConfirmModal').modal('hide'); 
    }

	async confirmDelete() {
        if (this.currentFile) {
            try {
                const files = this.files.filter(file => file.id !== this.currentFile.id);
				const fileIndex = this.files.findIndex((file) => file.id === this.currentFile.id);
				if (fileIndex !== -1) {
					await this.operations.removeRecord(this.props.value.records[fileIndex]);
					this.files = [...files]
					this.notification.add("Xóa file thành công.", {
						title: this.env._t("Success"),
						type: "success",
					});
				}
				else{
					this.notification.add("Không tìm thấy file.", {
						title: this.env._t("Error"),
						type: "danger",
					});
				}
            } catch (error) {
                this.notification.add(error.message || "Xóa file thất bại.", {
                    title: this.env._t("Error"),
                    type: "danger",
                });
            } finally {
                this.closeDeleteConfirmModal();
            }
        }
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
				const fileIndex = this.files.findIndex((file) => file.id === updatedFile.id);
				if (fileIndex !== -1) {
					await this.operations.updateRecord(this.props.value.records[fileIndex]);
					this.files[fileIndex].name = newName;
					this.closeRenameModal();
					this.notification.add("Đổi tên thành công.", {
						title: this.env._t("Success"),
						type: "success",
					});
				}
				else{
					this.notification.add("Không tìm thấy file.", {
						title: this.env._t("Error"),
						type: "danger",
					});
				}
            } catch (error) {
                this.notification.add(error.message || "Đổi tên thất bị.", {
                    title: this.env._t("Error"),
                    type: "danger",
                });
            }
        } else {
            this.notification.add("Ô tên không được để trống.", {
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
