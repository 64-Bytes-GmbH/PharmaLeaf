const createLiveOrderTemplate = () => {
    let template = '<tr class="list_element" data-id="">\
                        <td class="name">25/1 Amici-Cannabisblüten</td>\
                        <td class="cultivar">Icecream Cake Kush Mints</td>\
                        <td><span class="thc"></span>%</td>\
                        <td><span class="cbd"></span>%</td>\
                        <td>\
                            <div class="d-flex mx-auto">\
                                <img loading="lazy" class="genetic_img my-auto" src="" alt="Genetik Icon">\
                                <p class="ms-2 my-auto genetic">Hybridt Indica-dominant</p>\
                            </div>\
                        </td>\
                        <td class="manufacturer">Kineo Medical</td>\
                        <td>\
                            <img loading="lazy" class="treatment_img treatment treatment_value" value="" role="button" src="" alt="Behandlungsart Icon" data-bs-toggle="tooltip" data-bs-title="Unbestrahlt">\
                        </td>\
                        <td>\
                            <div class="status" value="2">\
                                <span class="status_display">Sofort verfügbar</span>\
                            </div>\
                        </td>\
                        <td class="price_value is_authenticated" is_authenticated="" value="">\
                            <span class="price"></span>\
                        </td>\
                        <td>\
                            <a href="javascript:void(0)" class="product_id" product="" onclick="addListItemToCart(this)" data-bs-toggle="tooltip" data-bs-title="In den Warenkorb">\
                                <img loading="lazy" class="cart_icon" src="" alt="Warenkorb Icon">\
                            </a>\
                        </td>\
                    </tr>'

    return template
}

const createTileProductsTemplate = () => {

    let template = '<div class="product product-tile list_element" data-id="">\
                        <div>\
                            <div class="product-img">\
                                <img class="img" loading="lazy" src="" lazy="lazyload" alt="">\
                            </div>\
                            <div class="product-info">\
                                <div>\
                                    <div>\
                                        <h1 class="name"></h1>\
                                        <h2 class="cultivar"></h2>\
                                        <h2 class="genetic"></h2>\
                                    </div>\
                                    <div>\
                                        <div class="status-div">\
                                            <p class="product-status status" value="">\
                                                <span class="status_display"></span>\
                                            </p>\
                                        </div>\
                                        <div class="price-div price_value d-flex">\
                                            <p class="is_authenticated my-auto me-auto text-start" is_authenticated="" value="">ab <span class="price"></span></p>\
                                            <a href="javascript:void(0)" class="product_id add-to-cart" product="" onclick="addListItemToCart(this)" data-bs-toggle="tooltip" data-bs-title="In den Warenkorb">\
                                                <img loading="lazy" class="cart_icon" src="" alt="Warenkorb Icon">\
                                            </a>\
                                        </div>\
                                    </div>\
                                </div>\
                                <div>\
                                    <div>\
                                        <div class="single-product-detail"><p>THC <b><span class="thc"></span> %</b></p></div>\
                                        <div class="single-product-detail"><p>CBD <b><span class="cbd"></span> %</b></p></div>\
                                    </div>\
                                    <div class="icons">\
                                        <img loading="lazy" class="genetic_img my-auto" src="" alt="Genetik Icon">\
                                        <img loading="lazy" class="treatment_img treatment treatment_value my-auto" value="" role="button" src="" alt="Behandlungsart Icon" data-bs-toggle="tooltip" data-bs-title="Unbestrahlt">\
                                    </div>\
                                </div>\
                            </div>\
                        </div>\
                    </div>'

    return template
}