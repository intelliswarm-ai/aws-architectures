package ai.intelliswarm.inventory.controller;

import ai.intelliswarm.inventory.service.ProductService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
@RequiredArgsConstructor
public class WebController {

    private final ProductService productService;

    @GetMapping("/")
    public String home(Model model) {
        model.addAttribute("inventoryValue", productService.calculateTotalInventoryValue());
        model.addAttribute("reorderProducts", productService.findProductsNeedingReorder());
        return "index";
    }

    @GetMapping("/products")
    public String products(Model model) {
        model.addAttribute("products", productService.findAll(PageRequest.of(0, 50, Sort.by("name"))));
        return "products/list";
    }

    @GetMapping("/login")
    public String login() {
        return "login";
    }
}
