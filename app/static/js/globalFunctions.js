const modalCenterOptions = {
    placement: 'bottom-right',
    backdrop: false,
    closable: true,
};

const toggleModal = (modalId, options=null) => {
    const modal = new Modal(document.getElementById(modalId), options);
    modal.show();
}

const hideModal = (modalId, options=null) => {
    const modal = new Modal(document.getElementById(modalId), options);
    modal.hide();
    
    $('[modal-backdrop]').remove();
}