function (doc) {
  if (doc.doc_type == 'ProjectSection') {
    emit([doc.account_id, doc.project_id, doc.section_type, doc.mod], null);
  }
}