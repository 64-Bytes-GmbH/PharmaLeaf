const createCartTemplate = (product, editable=true) => {

    let template = '<div class="cart-product" product-id="' + product.id + '" editable="' + editable + '">\
                        <div class="d-flex flex-row mb-1 mb-sm-3">\
                            <div class="me-2">\
                                <img src="' + product.img + '">\
                            </div>\
                            <div class="product-info flex-fill d-flex flex-column">\
                                <div class="flex-fill d-flex flex-column">\
                                    <h1>' + product.name + '</h1>\
                                </div>\
                                <div visible="' + product.preparedVisible + '">\
                                    <select class="form-select" onchange="changePrepared(this, ' + product.id + ')" name="prepared" aria-label="Abgabeform">\
                                        <option value="false">unverändert</option>\
                                        <option value="true">zerkleinert</option>\
                                    </select>\
                                </div>\
                            </div>\
                            <div>\
                                <a onclick="deleteProduct(' + product.id + ')" class="delete-button"></a>\
                            </div>\
                        </div>\
                        <div class="d-flex flex-row justify-content-between mb-4 product-price">\
                            <div class="d-flex">\
                                <div class="product-amount d-flex mr-2">\
                                    <input class="text-end" style="width: 80px" type="text" name="productAmount" onchange="changeProductAmount(this.value, ' + product.id + ')" value="' + product.amount + '">\
                                    <span class="ms-1">' + product.unit + '</span>\
                                </div>\
                            </div>\
                            <p class="m-0 price" value="' + product.total_value + '">' + product.total + ' (Brutto)</p>\
                        </div>\
                    </div>'

    return template
}

const dashBoardProducts = (product, orderNumber=null) => {
    
    let template = '<div id="orderProduct-' + product.id + '" product-id="' + product.id + '" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500">\
                        <div class="grid gap-4 sm:col-span-2 md:gap-6 sm:grid-cols-2 mb-3">\
                            <div>\
                                <label for="product' + product.id + '" class="inline-flex items-center mb-2 text-sm font-medium text-gray-900 dark:text-white">\
                                    Produkt\
                                </label>\
                                <select id="product' + product.id + '" name="product" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500">\
                                </select>\
                            </div>\
                            <div class="ml-auto flex flex-row gap-4">\
                                <p class="pr-1.5 ml-auto text-lg font-medium text-gray-900 dark:text-white">\
                                    Preis: <span class="text-gray-900 dark:text-gray-300" name="productPrice">' + product.total + '</span>\
                                </p>\
                                <button type="button" onclick="deleteOrderProduct(' + product.id + ', \'' + product.name + '\', \'' + orderNumber + '\')" data-modal-target="product-delete-popup-modal" data-modal-toggle="product-delete-popup-modal" class="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm p-1.5 ml-auto mb-auto inline-flex dark:hover:bg-gray-600 dark:hover:text-white" data-modal-toggle="orderModal">\
                                    <svg class="w-5 h-5 text-red-700 dark:text-red-500" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">\
                                        <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 7h14m-9 3v8m4-8v8M10 3h4a1 1 0 0 1 1 1v3H9V4a1 1 0 0 1 1-1ZM6 7h12v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V7Z"/>\
                                    </svg>\
                                    <span class="sr-only">Produkt löschen</span>\
                                </button>\
                            </div>\
                        </div>\
                        <div class="grid gap-4 sm:col-span-2 md:gap-6 sm:grid-cols-4">\
                            <div>\
                                <label for="prepared' + product.id + '" class="inline-flex items-center mb-2 text-sm font-medium text-gray-900 dark:text-white">\
                                    Abgabeform\
                                </label>\
                                <select id="prepared' + product.id + '" name="prepared" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500">\
                                </select>\
                            </div>\
                            <div>\
                                <label for="productAmount' + product.id + '" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white" name="productAmountLabel">' + product.amountLabel + '</label>\
                                <input type="number" name="productAmount" id="productAmount' + product.id + '" value="' + product.amount + '" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500" placeholder="Beispiel: 12">\
                            </div>\
                            <div>\
                                <label for="form' + product.id + '" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Form</label>\
                                <input type="text" name="form" id="form' + product.id + '" value="' + product.form + '" disabled class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500" placeholder="">\
                            </div>\
                            <div>\
                                <label for="supplier' + product.id + '" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white" name="productAmountLabel">Lieferant</label>\
                                <input type="text" name="supplier" id="supplier' + product.id + '" value="' + product.supplier + '" disabled class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500" placeholder="Beispiel: 12">\
                            </div>\
                        </div>\
                    </div>'

    return template;

}
