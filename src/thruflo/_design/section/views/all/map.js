function (doc) {
  if (doc.doc_type == 'Section') {
    emit([doc.account_id, doc.parent_id, doc.section_type, doc.mod], null);
  }
}
